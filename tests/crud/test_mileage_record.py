from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.mileage_record import (
    create_mileage_record,
    get_latest_mileage_record,
    get_mileage_record_by_id,
    list_mileage_records_by_vehicle,
    update_mileage_record,
)
from app.schemas.mileage_record import (
    MileageRecordCreate,
    MileageRecordUpdate,
)


async def test_create_mileage_record(db_session: AsyncSession, make_vehicle) -> None:
    """Создание записи одометра."""
    vehicle = await make_vehicle()

    record = await create_mileage_record(
        db_session,
        vehicle_id=vehicle.id,
        record_in=MileageRecordCreate(
            record_date=date(2026, 10, 1),
            mileage_km=152_340,
            source="manual",
            notes="Снял с одометра",
        ),
    )

    assert record.id is not None
    assert record.vehicle_id == vehicle.id
    assert record.record_date == date(2026, 10, 1)
    assert record.mileage_km == 152_340
    assert record.source == "manual"
    assert record.notes == "Снял с одометра"


async def test_create_mileage_record_minimal(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Минимальный набор полей."""
    vehicle = await make_vehicle()

    record = await create_mileage_record(
        db_session,
        vehicle_id=vehicle.id,
        record_in=MileageRecordCreate(
            record_date=date(2026, 10, 1),
            mileage_km=100_000,
        ),
    )

    assert record.source == "manual"
    assert record.driver_id is None
    assert record.notes is None


async def test_create_mileage_record_zero_km(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Пробес 0 допустим."""
    vehicle = await make_vehicle()

    record = await create_mileage_record(
        db_session,
        vehicle_id=vehicle.id,
        record_in=MileageRecordCreate(
            record_date=date(2026, 10, 1),
            mileage_km=0,
        ),
    )

    assert record.mileage_km == 0


async def test_create_mileage_record_negative_km_raises() -> None:
    """Отрицательный пробег → ошибка валидации."""
    with pytest.raises(ValidationError):
        MileageRecordCreate(
            record_date=date(2026, 10, 1),
            mileage_km=-100,
        )


async def test_create_mileage_record_vehicle_not_found_raises(
    db_session: AsyncSession,
) -> None:
    """Несуществующий vehicle_id -> IntegrityError."""
    with pytest.raises(IntegrityError):
        await create_mileage_record(
            db_session,
            vehicle_id=999_999,
            record_in=MileageRecordCreate(
                record_date=date(2026, 10, 1),
                mileage_km=100_000,
            ),
        )
    await db_session.rollback()


async def test_get_mileage_record_by_id(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Получение по id."""
    vehicle = await make_vehicle()
    created = await make_mileage_record(vehicle=vehicle)

    found = await get_mileage_record_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.vehicle_id == vehicle.id


async def test_get_mileage_record_by_id_not_found(
    db_session: AsyncSession,
) -> None:
    """Несуществующий id → None."""
    found = await get_mileage_record_by_id(db_session, 999_999)

    assert found is None


async def test_list_mileage_records_empty(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Нет записей → пустой список."""
    vehicle = await make_vehicle()

    records = await list_mileage_records_by_vehicle(db_session, vehicle.id)

    assert records == []


async def test_list_mileage_records_returns_all(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Возвращает все записи машины."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle)
    await make_mileage_record(vehicle=vehicle)
    await make_mileage_record(vehicle=vehicle)

    records = await list_mileage_records_by_vehicle(db_session, vehicle.id)

    assert len(records) == 3


async def test_list_mileage_records_ordered_desc(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Свежие вперёд (по дате DESC)."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 1, 1))
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 6, 1))
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 3, 1))

    records = await list_mileage_records_by_vehicle(db_session, vehicle.id)

    assert records[0].record_date == date(2026, 6, 1)
    assert records[1].record_date == date(2026, 3, 1)
    assert records[2].record_date == date(2026, 1, 1)


async def test_list_mileage_records_only_own_vehicle(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Возвращает только записи конкретной машины."""
    v1 = await make_vehicle()
    v2 = await make_vehicle()
    await make_mileage_record(vehicle=v1)
    await make_mileage_record(vehicle=v2)
    await make_mileage_record(vehicle=v2)

    records = await list_mileage_records_by_vehicle(db_session, v1.id)

    assert len(records) == 1
    assert records[0].vehicle_id == v1.id


async def test_list_mileage_records_pagination(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """skip/limit работают."""
    vehicle = await make_vehicle()
    r1 = await make_mileage_record(vehicle=vehicle, record_date=date(2026, 1, 1))
    r2 = await make_mileage_record(vehicle=vehicle, record_date=date(2026, 2, 1))
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 3, 1))

    page = await list_mileage_records_by_vehicle(
        db_session, vehicle.id, skip=1, limit=1
    )

    assert len(page) == 1
    assert page[0].id == r2.id
    assert r1.id != r2.id


async def test_get_latest_mileage_record(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Возвращает самую свежую запись."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 1, 1))
    latest = await make_mileage_record(vehicle=vehicle, record_date=date(2026, 10, 1))
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 5, 1))

    found = await get_latest_mileage_record(db_session, vehicle.id)

    assert found is not None
    assert found.id == latest.id
    assert found.record_date == date(2026, 10, 1)


async def test_get_latest_mileage_record_none(
    db_session: AsyncSession, make_vehicle
) -> None:
    """Нет записей → None."""
    vehicle = await make_vehicle()

    found = await get_latest_mileage_record(db_session, vehicle.id)

    assert found is None


async def test_update_mileage_record_mileage(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Обновление пробега."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(vehicle=vehicle, mileage_km=100_000)

    updated = await update_mileage_record(
        db_session, record, MileageRecordUpdate(mileage_km=100_500)
    )

    assert updated.mileage_km == 100_500


async def test_update_mileage_record_source(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Обновление source."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(vehicle=vehicle, source="manual")

    updated = await update_mileage_record(
        db_session, record, MileageRecordUpdate(source="gps")
    )

    assert updated.source == "gps"


async def test_update_mileage_record_notes_null(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """Явная передача notes=None стирает поле."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(vehicle=vehicle, notes="важное")
    assert record.notes == "важное"

    updated = await update_mileage_record(
        db_session, record, MileageRecordUpdate(notes=None)
    )

    assert updated.notes is None


async def test_update_mileage_record_empty_patch(
    db_session: AsyncSession, make_vehicle, make_mileage_record
) -> None:
    """PATCH {} не меняет ничего."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(
        vehicle=vehicle, mileage_km=100_000, source="manual"
    )
    original_km = record.mileage_km
    original_source = record.source

    updated = await update_mileage_record(db_session, record, MileageRecordUpdate())

    assert updated.mileage_km == original_km
    assert updated.source == original_source
