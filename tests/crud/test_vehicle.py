from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.vehicle import (
    create_vehicle,
    get_vehicle_by_id,
    get_vehicle_by_plate,
    list_vehicles,
    update_vehicle,
)
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


async def test_create_vehicle(db_session: AsyncSession) -> None:
    """Создание техники со всеми полями."""
    vehicle = await create_vehicle(
        db_session,
        VehicleCreate(
            plate_number="О957АУ",
            vin="XTA1234567890ABCD",
            brand="Mercedes",
            model="Arocs",
            year=2023,
            vehicle_type="dump_truck",
            capacity_kg=30000,
            volume_m3=Decimal("20.00"),
        ),
    )
    assert vehicle.id is not None
    assert vehicle.plate_number == "О957АУ"
    assert vehicle.vin == "XTA1234567890ABCD"
    assert vehicle.brand == "Mercedes"
    assert vehicle.year == 2023
    assert vehicle.vehicle_type == "dump_truck"
    assert vehicle.capacity_kg == 30000
    assert vehicle.volume_m3 == Decimal("20.00")
    assert vehicle.status == "active"


async def test_create_vehicle_normalizes_plate(db_session: AsyncSession) -> None:
    """plate_number приводится к верхнему регистру без пробелов."""
    vehicle = await create_vehicle(
        db_session,
        VehicleCreate(
            plate_number="   о957ау   ",
            vin="XTA1234567890ABCD",
            brand="Mercedes",
            model="Arocs",
            year=2023,
            vehicle_type="dump_truck",
        ),
    )
    assert vehicle.plate_number == "О957АУ"


async def test_create_vehicle_normalizes_vin(db_session: AsyncSession) -> None:
    """VIN приводится к верхнему регистру."""
    vehicle = await create_vehicle(
        db_session,
        VehicleCreate(
            plate_number="О957АУ",
            vin="z9m96423150473830",
            brand="Mercedes",
            model="Arocs",
            year=2023,
            vehicle_type="dump_truck",
        ),
    )

    assert vehicle.vin == "Z9M96423150473830"


async def test_create_vehicle_duplicate_plate(db_session: AsyncSession) -> None:
    """Дубликат plate_number -> IntegrityError."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }
    await create_vehicle(db_session, VehicleCreate(**payload))

    with pytest.raises(IntegrityError):
        await create_vehicle(
            db_session,
            VehicleCreate(
                **{**payload, "vin": "XTA9999999999ZZZZ"},
            ),
        )
    await db_session.rollback()


async def test_create_vehicle_duplicate_vin(db_session: AsyncSession) -> None:
    """Дубликат vin -> IntegrityError."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }
    await create_vehicle(db_session, VehicleCreate(**payload))

    with pytest.raises(IntegrityError):
        await create_vehicle(
            db_session,
            VehicleCreate(
                **{**payload, "plate_number": "А999БВ"},
            ),
        )
    await db_session.rollback()


async def test_get_vehicle_by_id(db_session: AsyncSession, make_vehicle) -> None:
    """Получение техники по id."""
    created = await make_vehicle()

    found = await get_vehicle_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.plate_number == created.plate_number


async def test_get_vehicle_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id -> None."""
    found = await get_vehicle_by_id(db_session, 999999)

    assert found is None


async def test_get_vehicle_by_plate(db_session: AsyncSession, make_vehicle) -> None:
    """Получение техники по госномеру."""
    created = await make_vehicle(plate_number="О957АУ")

    found = await get_vehicle_by_plate(db_session, "О957АУ")

    assert found is not None
    assert found.id == created.id


async def test_get_vehicle_by_plate_not_found(db_session: AsyncSession) -> None:
    """Несуществующий госномер -> None."""
    found = await get_vehicle_by_plate(db_session, "Х000ХХ")

    assert found is None


async def test_list_vehicle_empty(db_session: AsyncSession) -> None:
    """Пустая БД -> пустой список."""
    vehicle = await list_vehicles(db_session)

    assert vehicle == []


async def test_list_vehicles_pagination(db_session: AsyncSession, make_vehicle) -> None:
    """skip/limit работают."""
    v1 = await make_vehicle()
    v2 = await make_vehicle()
    await make_vehicle()

    page = await list_vehicles(db_session, skip=1, limit=1)

    assert len(page) == 1
    assert page[0].id == v2.id
    assert v1.id != v2.id


async def test_list_vehicles_filter_by_status(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Фильтр по status работает."""
    await make_vehicle(status="active")
    await make_vehicle(status="active")
    await make_vehicle(status="repair")

    active_only = await list_vehicles(db_session, status="active")
    repair_only = await list_vehicles(db_session, status="repair")

    assert len(active_only) == 2
    assert len(repair_only) == 1
    assert all(v.status == "active" for v in active_only)


async def test_update_vehicle_brand(db_session: AsyncSession, make_vehicle) -> None:
    """Обновление одной колонки."""
    vehicle = await make_vehicle(brand="Mercedes")

    updated = await update_vehicle(db_session, vehicle, VehicleUpdate(brand="Volvo"))

    assert updated.brand == "Volvo"


async def test_update_vehicle_plate_normalized(
    db_session: AsyncSession, make_vehicle
) -> None:
    """plate_number при update тоже нормализуется."""
    vehicle = await make_vehicle(plate_number="А001АА")

    updated = await update_vehicle(
        db_session, vehicle, VehicleUpdate(plate_number="  б002бб  ")
    )

    assert updated.plate_number == "Б002ББ"


async def test_update_vehicle_multiple_fields(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Обновление нескольких полей сразу."""
    vehicle = await make_vehicle()

    updated = await update_vehicle(
        db_session,
        vehicle,
        VehicleUpdate(brand="Volvo", model="FMX", year=2024),
    )

    assert updated.brand == "Volvo"
    assert updated.model == "FMX"
    assert updated.year == 2024


async def test_update_vehicle_empty_patch(
    db_session: AsyncSession, make_vehicle
) -> None:
    """PATCH {} не меняет ничего."""
    vehicle = await make_vehicle(brand="Mercedes", model="Arocs", year=2024)
    original_brand = vehicle.brand
    original_model = vehicle.model
    original_year = vehicle.year

    updated = await update_vehicle(db_session, vehicle, VehicleUpdate())

    assert updated.brand == original_brand
    assert updated.model == original_model
    assert updated.year == original_year


async def test_update_vehicle_notes_null(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Явная передача notes=None стирает поле."""
    vehicle = await make_vehicle(notes="важная заметка")
    assert vehicle.notes == "важная заметка"

    updated = await update_vehicle(db_session, vehicle, VehicleUpdate(notes=None))

    assert updated.notes is None


async def test_update_vehicle_status(db_session: AsyncSession, make_vehicle) -> None:
    """Обновление статуса."""
    vehicle = await make_vehicle(status="active")

    updated = await update_vehicle(db_session, vehicle, VehicleUpdate(status="repair"))

    assert updated.status == "repair"


async def test_create_vehicle_with_fuel_consumption(
    db_session: AsyncSession,
) -> None:
    """Создание с расходом топлива."""
    vehicle = await create_vehicle(
        db_session,
        VehicleCreate(
            plate_number="О957АУ",
            vin="XTA1234567890ABCD",
            brand="Mercedes",
            model="Arocs",
            year=2023,
            vehicle_type="dump_truck",
            fuel_consumption_per_100km=Decimal("35.50"),
        ),
    )
    assert vehicle.fuel_consumption_per_100km == Decimal("35.50")
    assert vehicle.fuel_consumption_per_hour is None


async def test_update_vehicle_fuel_consumption(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Обновление расхода."""
    vehicle = await make_vehicle(fuel_consumption_per_100km=None)

    updated = await update_vehicle(
        db_session,
        vehicle,
        VehicleUpdate(fuel_consumption_per_100km=Decimal("40.00")),
    )

    assert updated.fuel_consumption_per_100km == Decimal("40.00")
