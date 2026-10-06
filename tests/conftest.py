"""Общие фикстуры для тестов.

Тестовая БД — отдельный Postgres-контейнер (порт 5433,
см. docker-compose.test.yml). Переменные читаются из .env.test.

Схема накатывается Alembic-миграциями один раз при старте pytest —
в хуке pytest_configure, до того как pytest-asyncio откроет event loop.
Каждый тест выполняется в своей транзакции и откатывается после
завершения — благодаря SAVEPOINT-паттерну SQLAlchemy БД остаётся чистой,
а тесты независимы друг от друга.
"""

import itertools
import os
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.crud.material import create_material, update_material
from app.crud.vehicle import create_vehicle
from app.models.driver import Driver
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.schemas.vehicle import VehicleCreate

# .env.test читаем ДО импорта app.* — иначе Settings создастся
# с dev-настройками из .env, и мы не сможем переопределить URL.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env.test", override=True)


# --- Импорты приложения — после .env.test ---
from app.crud.driver import create_driver, update_driver  # noqa: E402
from app.crud.driver_absence import create_absence  # noqa: E402
from app.database.session import session_getter  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.driver import DriverCreate, DriverUpdate  # noqa: E402
from app.schemas.driver_absence import DriverAbsenceCreate  # noqa: E402


def _build_test_database_url() -> str:
    """Собирает TEST_DATABASE_URL из переменных окружения .env.test.

    Формат совпадает с Settings.database_url (psycopg, async).
    Если в .env.test задан TEST_DATABASE_URL — используется он.
    """
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return explicit

    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    db = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


TEST_DATABASE_URL = _build_test_database_url()


def pytest_configure(config):
    """Накатывает Alembic-миграции на тестовую БД ДО старта event loop.

    pytest_configure вызывается один раз при старте pytest, до сбора
    тестов и до того, как pytest-asyncio откроет свой event loop.
    Значит, alembic может спокойно вызвать asyncio.run() внутри себя.
    """
    from alembic.config import Config

    from alembic import command

    alembic_cfg = Config(str(_PROJECT_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Async-движок к тестовой БД. Один на всю сессию тестов.

    echo=False — иначе SQL-логи утопят вывод pytest.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(test_engine) -> AsyncGenerator[AsyncConnection]:
    """Соединение к тестовой БД с открытой внешней транзакцией.

    Все commit() внутри теста попадают в SAVEPOINT, а не в эту
    транзакцию. После теста она откатывается — БД чистая.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def db_session(db_connection) -> AsyncGenerator[AsyncSession]:
    """AsyncSession, привязанная к внешней транзакции через SAVEPOINT.

    join_transaction_mode='create_savepoint' — ключевой параметр:
    без него commit() внутри CRUD отправит данные в outer transaction,
    и rollback в фикстуре выше не спасёт.
    """
    session_maker = async_sessionmaker(
        bind=db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient]:
    """httpx.AsyncClient, ходящий в FastAPI через ASGITransport.

    Подменяет зависимость session_getter на тестовую сессию через
    app.dependency_overrides. Роутеры этого не замечают.
    """

    async def _override_session_getter() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[session_getter] = _override_session_getter

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Фабрика Vehicle для тестов ---

_vehicle_counter = itertools.count(1)


@pytest_asyncio.fixture
async def make_vehicle(db_session):
    """Фабрика техники для тестов."""

    async def _make(**overrides):
        n = next(_vehicle_counter)
        data = {
            "plate_number": f"ТЕСТ{n:04d}",
            "vin": f"VIN{n:014d}",
            "brand": "Mercedes",
            "model": "Arocs",
            "year": 2023,
            "vehicle_type": "dump_truck",
            "capacity_kg": 30000,
            "volume_m3": Decimal("20.00"),
        }
        data.update(overrides)
        return await create_vehicle(db_session, VehicleCreate(**data))

    return _make


_driver_counter = itertools.count(1)
_absence_counter = itertools.count(1)


async def _create_driver_helper(db_session: AsyncSession) -> "Driver":
    """Внутренний хелпер — создать тестового водителя с уникальным phone."""
    n = next(_driver_counter)
    return await create_driver(
        db_session,
        DriverCreate(
            last_name=f"Фамилия{n}",
            first_name=f"Имя{n}",
            middle_name=f"Отчество{n}",
            phone=f"+7978{n:07d}",
        ),
    )


@pytest_asyncio.fixture
async def make_driver(db_session):
    """Фабрика водителей для тестов."""

    async def _make(**overrides):
        status_value = overrides.pop("status", None)
        n = next(_driver_counter)
        data = {
            "last_name": f"Фамилия{n}",
            "first_name": f"Имя{n}",
            "middle_name": f"Отчество{n}",
            "phone": f"+7900{n:07d}",
        }
        data.update(overrides)
        driver = await create_driver(db_session, DriverCreate(**data))
        if status_value is not None:
            driver = await update_driver(
                db_session, driver, DriverUpdate(status=status_value)
            )
        return driver

    return _make


@pytest_asyncio.fixture
async def make_absence(db_session):
    """Фабрика отсутствий для тестов.

    Если driver не передан — создаёт нового водителя.
    """

    async def _make(driver=None, **overrides):
        if driver is None:
            driver = await _create_driver_helper(db_session)
        n = next(_absence_counter)
        base = date(2026, 1, 1)
        data = {
            "absence_type": "vacation",
            "date_from": base,
            "date_to": base + timedelta(days=3 + (n % 20)),
            "reason": f"Отпуск {n}",
        }
        data.update(overrides)
        return await create_absence(
            db_session,
            driver_id=driver.id,
            absence_in=DriverAbsenceCreate(**data),
        )

    return _make


_material_counter = itertools.count(1)


@pytest_asyncio.fixture
async def make_material(db_session):
    """Фабрика материалов для тестов.

    Поле status НЕ входит в MaterialCreate (создание всегда active),
    поэтому если status передан явно — догоняем через update_material.
    """

    async def _make(**overrides):
        status_value = overrides.pop("status", None)
        n = next(_material_counter)
        data = {
            "name": f"Материал {n}",
            "material_type": "inert",
            "unit": "ton",
            "is_bulk": True,
        }
        data.update(overrides)
        material = await create_material(db_session, MaterialCreate(**data))
        if status_value is not None:
            material = await update_material(
                db_session, material, MaterialUpdate(status=status_value)
            )
        return material

    return _make
