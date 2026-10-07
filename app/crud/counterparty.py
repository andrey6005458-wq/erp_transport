from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.counterparty import Counterparty
from app.schemas.counterparty import CounterpartyCreate, CounterpartyUpdate


async def create_counterparty(
    db: AsyncSession,
    counterparty_in: CounterpartyCreate,
) -> Counterparty:
    """Создать контрагента."""
    counterparty = Counterparty(**counterparty_in.model_dump())
    db.add(counterparty)
    await db.commit()
    await db.refresh(counterparty)
    return counterparty


async def get_counterparty_by_id(
    db: AsyncSession,
    counterparty_id: int,
) -> Counterparty | None:
    """Возвращает контрагента по primary key."""
    return await db.get(Counterparty, counterparty_id)


async def get_counterparty_by_name(
    db: AsyncSession,
    name: str,
) -> Counterparty | None:
    """Возвращает контрагента по имени."""
    stmt = select(Counterparty).where(Counterparty.name == name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_counterparties(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    counterparty_type: str | None = None,
    search: str | None = None,
) -> list[Counterparty]:
    """Возвращает страницу контрагентов с фильтрами."""
    stmt = select(Counterparty).order_by(Counterparty.name).offset(skip).limit(limit)
    if status is not None:
        stmt = stmt.where(Counterparty.status == status)
    if counterparty_type is not None:
        stmt = stmt.where(Counterparty.counterparty_type == counterparty_type)
    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Counterparty.name.ilike(pattern),
                Counterparty.inn.ilike(pattern),
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_counterparty(
    db: AsyncSession,
    counterparty: Counterparty,
    counterparty_in: CounterpartyUpdate,
) -> Counterparty:
    """Частично обновить контрагента по PATCH семантике."""
    update_data = counterparty_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(counterparty, field, value)
    await db.commit()
    await db.refresh(counterparty)
    return counterparty
