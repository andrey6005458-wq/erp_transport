import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.driver import (
    create_driver,
    get_driver_by_id,
    get_driver_by_phone,
    list_drivers,
    update_driver,
)
from app.schemas.driver import DriverCreate, DriverUpdate


async def test_create_driver(db_session: AsyncSession) -> None:
    """Создание водителя со всеми полями."""
    driver = await create_driver(
        db_session,
        DriverCreate(
            last_name="Фомин",
            first_name="Дмитрий",
            middle_name="Александрович",
            phone="+79781234567",
            notes="Водитель самосвала",
        ),
    )
    assert driver.id is not None
    assert driver.last_name == "Фомин"
    assert driver.first_name == "Дмитрий"
    assert driver.middle_name == "Александрович"
    assert driver.phone == "+79781234567"
    assert driver.status == "active"
    assert driver.notes == "Водитель самосвала"


async def test_create_driver_without_middle_name(db_session: AsyncSession) -> None:
    """Отчество опционально."""
    driver = await create_driver(
        db_session,
        DriverCreate(
            last_name="Иванов",
            first_name="Иван",
            phone="+79781234567",
        ),
    )
    assert driver.middle_name is None


async def test_create_driver_normalizes_phone_8(db_session: AsyncSession) -> None:
    """8XXXXXXXXXX → +7XXXXXXXXXX."""
    driver = await create_driver(
        db_session,
        DriverCreate(
            last_name="Иванов",
            first_name="Иван",
            phone="89781234567",
        ),
    )
    assert driver.phone == "+79781234567"


async def test_create_driver_normalizes_phone_with_separators(
    db_session: AsyncSession,
) -> None:
    """+7 (978) 123-45-67 -> +79781234567."""
    driver = await create_driver(
        db_session,
        DriverCreate(
            last_name="Иванов",
            first_name="Иван",
            phone="+7 (978) 123-45-67",
        ),
    )
    assert driver.phone == "+79781234567"


async def test_create_driver_duplicate_phone(db_session: AsyncSession) -> None:
    """Дубликант phone -> IntergityError."""
    await create_driver(
        db_session,
        DriverCreate(
            last_name="Иванов",
            first_name="Иван",
            phone="+79781234567",
        ),
    )

    with pytest.raises(IntegrityError):
        await create_driver(
            db_session,
            DriverCreate(
                last_name="Петров",
                first_name="Петр",
                phone="+79781234567",
            ),
        )
    await db_session.rollback()


async def test_get_driver_by_id(db_session: AsyncSession, make_driver) -> None:
    """Получение водителя по id."""
    created = await make_driver()

    found = await get_driver_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.phone == created.phone


async def test_get_driver_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id -> None."""
    found = await get_driver_by_id(db_session, 999999)

    assert found is None


async def test_get_driver_by_phone(db_session: AsyncSession, make_driver) -> None:
    """Получение водителя по телефону."""
    created = await make_driver(phone="+79781234567")

    found = await get_driver_by_phone(db_session, "+79781234567")

    assert found is not None
    assert found.id == created.id


async def test_get_driver_by_phone_normalizes_input(
    db_session: AsyncSession, make_driver
) -> None:
    """8XXXXXXXXXX на входе → находит +7XXXXXXXXXX в БД."""
    created = await make_driver(phone="+79781234567")

    found = await get_driver_by_phone(db_session, "89781234567")

    assert found is not None
    assert found.id == created.id


async def test_get_driver_by_phone_with_separators(
    db_session: AsyncSession, make_driver
) -> None:
    """+7 (900) 123-45-67 на входе → находит."""
    created = await make_driver(phone="+79781234567")

    found = await get_driver_by_phone(db_session, "+7 (978) 123-45-67")

    assert found is not None
    assert found.id == created.id


async def test_get_driver_by_phone_not_found(db_session: AsyncSession) -> None:
    """Несуществующий телефон → None."""
    found = await get_driver_by_phone(db_session, "+79999999999")

    assert found is None


async def test_list_drivers_empty(db_session: AsyncSession) -> None:
    """Пустая БД → пустой список."""
    drivers = await list_drivers(db_session)

    assert drivers == []


async def test_list_drivers_returns_all(db_session: AsyncSession, make_driver) -> None:
    """Возвращает всех созданных."""
    await make_driver()
    await make_driver()
    await make_driver()

    drivers = await list_drivers(db_session)

    assert len(drivers) == 3


async def test_list_drivers_ordered_by_last_name(
    db_session: AsyncSession, make_driver
) -> None:
    """Сортировка по last_name, затем first_name."""
    await make_driver(last_name="Яковлев", first_name="Иван")
    await make_driver(last_name="Абрамов", first_name="Пётр")
    await make_driver(last_name="Абрамов", first_name="Антон")

    drivers = await list_drivers(db_session)

    assert drivers[0].last_name == "Абрамов"
    assert drivers[0].first_name == "Антон"
    assert drivers[1].first_name == "Пётр"
    assert drivers[2].last_name == "Яковлев"


async def test_list_drivers_pagination(db_session: AsyncSession, make_driver) -> None:
    """skil/limit работают."""
    d1 = await make_driver()
    d2 = await make_driver()
    await make_driver()

    page = await list_drivers(db_session, skip=1, limit=1)

    assert len(page) == 1
    assert page[0].id == d2.id
    assert d1.id != d2.id


async def test_list_drivers_filter_by_status(
    db_session: AsyncSession, make_driver
) -> None:
    """Фильтр по status."""
    await make_driver(status="active")
    await make_driver(status="active")
    await make_driver(status="fired")

    active_only = await list_drivers(db_session, status="active")
    fired_only = await list_drivers(db_session, status="fired")

    assert len(active_only) == 2
    assert len(fired_only) == 1
    assert all(d.status == "active" for d in active_only)


async def test_list_drivers_search_by_last_name(
    db_session: AsyncSession, make_driver
) -> None:
    """Поиск по фамилии."""
    await make_driver(last_name="Фомин", first_name="Дмитрий")
    await make_driver(last_name="Иванов", first_name="Иван")

    found = await list_drivers(db_session, search="Фом")

    assert len(found) == 1
    assert found[0].last_name == "Фомин"


async def test_list_drivers_search_by_first_name(
    db_session: AsyncSession, make_driver
) -> None:
    """Поиск по имени."""
    await make_driver(last_name="Фомин", first_name="Дмитрий")
    await make_driver(last_name="Иванов", first_name="иван")

    found = await list_drivers(db_session, search="Дмитр")

    assert len(found) == 1
    assert found[0].first_name == "Дмитрий"


async def test_list_drivers_search_by_middle_name(
    db_session: AsyncSession, make_driver
) -> None:
    """Поиск по отчеству."""
    await make_driver(
        last_name="Фомин", first_name="Дмитрий", middle_name="Александрович"
    )
    await make_driver(last_name="Иванов", first_name="иван", middle_name="Иванович")

    found = await list_drivers(db_session, search="Александрович")

    assert len(found) == 1
    assert found[0].middle_name == "Александрович"


async def test_list_drivers_search_case_insensitive(
    db_session: AsyncSession, make_driver
) -> None:
    """Поиск нечувствителен к регистру."""
    await make_driver(last_name="Фомин")

    found_lower = await list_drivers(db_session, search="фом")
    found_upper = await list_drivers(db_session, search="ФОМ")
    found_mixed = await list_drivers(db_session, search="Фом")

    assert len(found_lower) == 1
    assert len(found_upper) == 1
    assert len(found_mixed) == 1


async def test_list_drivers_search_no_results(
    db_session: AsyncSession, make_driver
) -> None:
    """Поиск без совпадений -> пустой список."""
    await make_driver(last_name="Фомин")

    found = await list_drivers(db_session, search="Несуществующий")

    assert found == []


async def test_update_driver_last_name(db_session: AsyncSession, make_driver) -> None:
    """Обновление одной колонки."""
    driver = await make_driver(last_name="Иванов")

    updated = await update_driver(db_session, driver, DriverUpdate(last_name="Фомин"))

    assert updated.last_name == "Фомин"


async def test_update_driver_phone_normalized(
    db_session: AsyncSession, make_driver
) -> None:
    """phone при update тоже нормализуется."""
    driver = await make_driver(phone="+79781234567")

    updated = await update_driver(
        db_session, driver, DriverUpdate(phone="8 (978) 111-22-33")
    )

    assert updated.phone == "+79781112233"


async def test_update_driver_multiple_fields(
    db_session: AsyncSession, make_driver
) -> None:
    """Обновление нескольких полей сразу."""
    driver = await make_driver()

    updated = await update_driver(
        db_session,
        driver,
        DriverUpdate(first_name="Иван", middle_name="Иванович", notes="Обновлен"),
    )

    assert updated.first_name == "Иван"
    assert updated.middle_name == "Иванович"
    assert updated.notes == "Обновлен"


async def test_update_driver_empty_patch(db_session: AsyncSession, make_driver) -> None:
    """PATCH {} не меняет ничего."""
    driver = await make_driver(last_name="Иванов", first_name="Иван")
    original_last = driver.last_name
    original_first = driver.first_name

    updated = await update_driver(db_session, driver, DriverUpdate())

    assert updated.last_name == original_last
    assert updated.first_name == original_first


async def test_update_driver_notes_null(db_session: AsyncSession, make_driver) -> None:
    """Явная передача notes=None стирает поле."""
    driver = await make_driver(notes="Важная заметка")
    assert driver.notes == "Важная заметка"

    updated = await update_driver(db_session, driver, DriverUpdate(notes=None))

    assert updated.notes is None


async def test_update_driver_status_fired(
    db_session: AsyncSession, make_driver
) -> None:
    """Смена статуса active -> fired."""
    driver = await make_driver(status="active")

    updated = await update_driver(db_session, driver, DriverUpdate(status="fired"))

    assert updated.status == "fired"
