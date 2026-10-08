from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.location import (
    create_location,
    get_location_by_id,
    get_location_by_name,
    list_locations,
    update_location,
)
from app.schemas.location import LocationCreate, LocationUpdate


async def test_create_location(db_session: AsyncSession) -> None:
    """Создание локации со всеми полями."""
    location = await create_location(
        db_session,
        LocationCreate(
            name="Карьер Шархинский",
            location_type="quarry",
            address="село Малый Маяк, территория Промышленная зона, 3",
            latitude=Decimal("44.611612"),
            longitude=Decimal("34.344047"),
            notes="Нерудные строительные материалы",
        ),
    )
    assert location.id is not None
    assert location.name == "Карьер Шархинский"
    assert location.location_type == "quarry"
    assert location.address == "село Малый Маяк, территория Промышленная зона, 3"
    assert location.latitude == Decimal("44.611612")
    assert location.longitude == Decimal("34.344047")
    assert location.status == "active"


async def test_create_location_minimal(db_session: AsyncSession) -> None:
    """Минимальный набор полей."""
    location = await create_location(
        db_session,
        LocationCreate(
            name="База",
            location_type="base",
        ),
    )
    assert location.id is not None
    assert location.address is None
    assert location.latitude is None
    assert location.longitude is None
    assert location.notes is None
    assert location.status == "active"


async def test_create_location_duplicate_name(db_session: AsyncSession) -> None:
    """Дубликат name -> IntergityError."""
    await create_location(
        db_session,
        LocationCreate(name="Карьер Зуйский", location_type="quarry"),
    )

    with pytest.raises(IntegrityError):
        await create_location(
            db_session,
            LocationCreate(name="Карьер Зуйский", location_type="dump"),
        )
    await db_session.rollback()


async def test_get_location_by_id(db_session: AsyncSession, make_location) -> None:
    """Получение по id."""
    created = await make_location()

    found = await get_location_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id


async def test_get_location_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id -> None."""
    found = await get_location_by_id(db_session, 999999)

    assert found is None


async def test_get_location_by_name(db_session: AsyncSession, make_location) -> None:
    """Получение по имени."""
    created = await make_location(name="Карьер Шархинский")

    found = await get_location_by_name(db_session, "Карьер Шархинский")

    assert found is not None
    assert found.id == created.id


async def test_get_location_by_name_not_found(db_session: AsyncSession) -> None:
    """Несуществующее имя -> None."""
    found = await get_location_by_name(db_session, "Несуществующая")

    assert found is None


async def test_list_locations_empty(db_session: AsyncSession) -> None:
    """Пустая БД -> пустой список."""
    result = await list_locations(db_session)

    assert result == []


async def test_list_locations_returns_all(
    db_session: AsyncSession, make_location
) -> None:
    """Возвращает все созданные."""
    await make_location()
    await make_location()
    await make_location()

    result = await list_locations(db_session)

    assert len(result) == 3


async def test_list_locations_ordered_by_name(
    db_session: AsyncSession, make_location
) -> None:
    """Сортировка по name."""
    await make_location(name="Карьер Ялтинский")
    await make_location(name="Карьер Алуштинский")
    await make_location(name="Карьер Балаклавский")

    result = await list_locations(db_session)

    assert result[0].name == "Карьер Алуштинский"
    assert result[1].name == "Карьер Балаклавский"
    assert result[2].name == "Карьер Ялтинский"


async def test_list_locations_pagination(
    db_session: AsyncSession, make_location
) -> None:
    """skip/limit работают."""
    l1 = await make_location(name="А")
    l2 = await make_location(name="Б")
    await make_location(name="В")

    page = await list_locations(db_session, skip=1, limit=1)

    assert len(page) == 1
    assert page[0].id == l2.id
    assert l1.id != l2.id


async def test_list_locations_filter_by_status(
    db_session: AsyncSession, make_location
) -> None:
    """Фильтр по status."""
    await make_location(status="active")
    await make_location(status="active")
    await make_location(status="archived")

    active_only = await list_locations(db_session, status="active")
    archived_only = await list_locations(db_session, status="archived")

    assert len(active_only) == 2
    assert len(archived_only) == 1
    assert all(loc.status == "active" for loc in active_only)


async def test_list_locations_filter_by_type(
    db_session: AsyncSession, make_location
) -> None:
    """Фильтр по location_type."""
    await make_location(location_type="quarry")
    await make_location(location_type="quarry")
    await make_location(location_type="dump")

    quarries = await list_locations(db_session, location_type="quarry")
    dumps = await list_locations(db_session, location_type="dump")

    assert len(quarries) == 2
    assert len(dumps) == 1


async def test_list_locations_search_by_name(
    db_session: AsyncSession, make_location
) -> None:
    """Поиск по name."""
    await make_location(name="Карьер Шархинский")
    await make_location(name="Карьер Балаклавский")
    await make_location(name="Объект: пгт. Гурзуф, ул. Ялтинская")

    found = await list_locations(db_session, search="Карьер")

    assert len(found) == 2


async def test_list_locations_search_by_address(
    db_session: AsyncSession, make_location
) -> None:
    """Поиск по address."""
    await make_location(
        name="Объект 1",
        address="г. Ялта, ул. Ленина 5",
    )
    await make_location(
        name="Объект 2",
        address="г. Симферополь, ул. Промышленная 5",
    )

    found = await list_locations(db_session, search="Ялта")

    assert len(found) == 1
    assert "Ялта" in found[0].address


async def test_list_locations_search_no_results(
    db_session: AsyncSession, make_location
) -> None:
    """Поиск без совпадений → пусто."""
    await make_location(name="Карьер")

    found = await list_locations(db_session, search="Несуществующий")

    assert found == []


async def test_update_location_name(db_session: AsyncSession, make_location) -> None:
    """Обновление name."""
    location = await make_location(name="Старое")

    updated = await update_location(db_session, location, LocationUpdate(name="Новое"))

    assert updated.name == "Новое"


async def test_update_location_status_archived(
    db_session: AsyncSession, make_location
) -> None:
    """Soft delete через status=archived."""
    location = await make_location(status="active")

    updated = await update_location(
        db_session, location, LocationUpdate(status="archived")
    )

    assert updated.status == "archived"


async def test_update_location_coordinates(
    db_session: AsyncSession, make_location
) -> None:
    """Обновление координат."""
    location = await make_location(latitude=None, longitude=None)

    updated = await update_location(
        db_session,
        location,
        LocationUpdate(
            latitude=Decimal("45.123456"),
            longitude=Decimal("34.567890"),
        ),
    )

    assert updated.latitude == Decimal("45.123456")
    assert updated.longitude == Decimal("34.567890")


async def test_update_location_empty_patch(
    db_session: AsyncSession, make_location
) -> None:
    """PATCH {} не меняет ничего."""
    location = await make_location(name="Карьер", location_type="quarry")
    original_name = location.name
    original_type = location.location_type

    updated = await update_location(db_session, location, LocationUpdate())

    assert updated.name == original_name
    assert updated.location_type == original_type


async def test_update_location_notes_null(
    db_session: AsyncSession, make_location
) -> None:
    """Явная передача notes=None стирает поле."""
    location = await make_location(notes="важная заметка")
    assert location.notes == "важная заметка"

    updated = await update_location(db_session, location, LocationUpdate(notes=None))

    assert updated.notes is None
