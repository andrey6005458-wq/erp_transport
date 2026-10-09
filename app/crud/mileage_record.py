
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mileage_record import MileageRecord
from app.schemas.mileage_record import MileageRecordCreate, MileageRecordUpdate


async def create_mileage_record(
    db: AsyncSession,
    vehicle_id: int,
    record_in: MileageRecordCreate,
) -> MileageRecord:
    """Создать запись одометра."""
    record = MileageRecord(vehicle_id=vehicle_id, **record_in.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_mileage_record_by_id(
    db: AsyncSession,
    record_id: int,
) -> MileageRecord | None:
    """Возвращает запись по primary key."""
    return await db.get(MileageRecord, record_id)


async def list_mileage_records_by_vehicle(
    db: AsyncSession,
    vehicle_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[MileageRecord]:
    """Возвращает записи одометра машины, свежие вперёд."""
    stmt = (
        select(MileageRecord)
        .where(MileageRecord.vehicle_id == vehicle_id)
        .order_by(MileageRecord.record_date.desc(), MileageRecord.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_latest_mileage_record(
    db: AsyncSession,
    vehicle_id: int,
) -> MileageRecord | None:
    """Возвращает последнюю (по дате) запись одометра."""
    stmt = (
        select(MileageRecord)
        .where(MileageRecord.vehicle_id == vehicle_id)
        .order_by(MileageRecord.record_date.desc(), MileageRecord.id.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_mileage_record(
    db: AsyncSession,
    record: MileageRecord,
    record_in: MileageRecordUpdate,
) -> MileageRecord:
    """Частично обновить запись по PATCH семантике."""
    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record

