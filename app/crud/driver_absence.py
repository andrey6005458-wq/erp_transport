from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_absence import DriverAbsence
from app.schemas.driver_absence import DriverAbsenceCreate, DriverAbsenceUpdate


async def _has_overlap(
    db: AsyncSession,
    driver_id: int,
    date_from: date,
    date_to: date | None,
    exclude_absence_id: int | None = None,
) -> bool:
    """Проверить, пересекается ли период с другими отсутствиями водителя."""
    end = date_to if date_to is not None else date(9999, 12, 31)
    stmt = select(DriverAbsence.id).where(
        DriverAbsence.driver_id == driver_id,
        or_(
            DriverAbsence.date_to.is_(None),
            DriverAbsence.date_to >= date_from,
        ),
        DriverAbsence.date_from <= end,
    )
    if exclude_absence_id is not None:
        stmt = stmt.where(DriverAbsence.id != exclude_absence_id)

    result = await db.execute(stmt.limit(1))
    return result.scalar_one_or_none() is not None


async def create_absence(
    db: AsyncSession,
    driver_id: int,
    absence_in: DriverAbsenceCreate,
) -> DriverAbsence:
    """Создать период отсутствия. Бросает ValueError при пересечении."""
    if await _has_overlap(
        db,
        driver_id=driver_id,
        date_from=absence_in.date_from,
        date_to=absence_in.date_to,
    ):
        raise ValueError(
            """У водителя уже есть отсутствие, пересекающееся с указанным периодом."""
        )

    absence = DriverAbsence(driver_id=driver_id, **absence_in.model_dump())
    db.add(absence)
    await db.commit()
    await db.refresh(absence)
    return absence


async def get_absence_by_id(db: AsyncSession, absence_id: int) -> DriverAbsence | None:
    """Возвращает отсутствие по primary key."""
    return await db.get(DriverAbsence, absence_id)


async def list_absences_by_driver(
    db: AsyncSession,
    driver_id: int,
    skip: int = 0,
    limit: int = 100,
    absence_type: str | None = None,
) -> list[DriverAbsence]:
    """Возвращает страницу отсутствий водителя с фильтром по типу."""
    stmt = (
        select(DriverAbsence)
        .where(DriverAbsence.driver_id == driver_id)
        .order_by(DriverAbsence.date_from.desc())
        .offset(skip)
        .limit(limit)
    )
    if absence_type is not None:
        stmt = stmt.where(DriverAbsence.absence_type == absence_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_absence(
    db: AsyncSession,
    absence: DriverAbsence,
    absence_in: DriverAbsenceUpdate,
) -> DriverAbsence:
    """Частично обновить отсутствие. Бросает ValueError при пересечении."""
    update_data = absence_in.model_dump(exclude_unset=True)

    new_from = update_data.get("date_from", absence.date_from)
    new_to = update_data.get("date_to", absence.date_to)

    if new_to is not None and new_to < new_from:
        raise ValueError("date_to не может быть раньше date_from.")

    if await _has_overlap(
        db,
        driver_id=absence.driver_id,
        date_from=new_from,
        date_to=new_to,
        exclude_absence_id=absence.id,
    ):
        raise ValueError(
            """Обновление создаёт пересечение с другим отсутствием водителя."""
        )

    for field, value in update_data.items():
        setattr(absence, field, value)

    await db.commit()
    await db.refresh(absence)
    return absence


async def delete_absence(db: AsyncSession, absence: DriverAbsence) -> None:
    """Удалить отсутствие."""
    await db.delete(absence)
    await db.commit()
