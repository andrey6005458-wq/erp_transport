"""Тесты для app/crud/user.py."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import verify_password
from app.crud.user import create_user, get_user_by_email, get_user_by_id
from app.schemas.user import UserCreate


async def test_create_user(db_session):
    """create_user создаёт пользователя с хешированным паролем."""
    user_in = UserCreate(
        email="alice@example.com",
        password="secret123",
        phone="+79990001122",
    )

    user = await create_user(db_session, user_in)

    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.phone == "+79990001122"
    assert user.hashed_password != "secret123"
    assert verify_password("secret123", user.hashed_password) is True
    assert user.is_active is True


async def test_create_user_duplicate_email(db_session):
    """create_user падает на дубликате email (UNIQUE constraint).

    IntegrityError — исключение SQLAlchemy на нарушение ограничений БД.
    После него сессия в невалидном состоянии, нужен rollback.
    """
    user_in = UserCreate(email="alice@example.com", password="secret123")

    await create_user(db_session, user_in)

    with pytest.raises(IntegrityError):
        await create_user(db_session, user_in)

    await db_session.rollback()


async def test_get_user_by_id(db_session):
    """get_user_by_id возвращает пользовалетя по id."""
    user_in = UserCreate(email="bob@example.com", password="secret123")

    created = await create_user(db_session, user_in)

    found = await get_user_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.email == "bob@example.com"


async def test_get_user_by_id_not_found(db_session):
    """get_user_by_id возвращает None, если пользователя нет."""
    found = await get_user_by_id(db_session, 99999)

    assert found is None


async def test_get_user_by_email(db_session):
    """get_user_by_email возвращает пользователя по email."""
    user_in = UserCreate(email="bob@example.com", password="secret123")

    created = await create_user(db_session, user_in)

    found = await get_user_by_email(db_session, created.email)

    assert found is not None
    assert found.email == "bob@example.com"


async def test_get_user_by_email_not_found(db_session):
    """get_user_by_email возвращает None, если email не найден."""
    found = await get_user_by_email(db_session, "nobody@example.com")

    assert found is None
