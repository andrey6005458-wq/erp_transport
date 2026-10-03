from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate
from app.utils.phone import normalize_phone


async def create_driver(db: AsyncSession, driver_in: DriverCreate) -> Driver:
    """Создает водителя. Phone уже нормализован в Pydantic."""
    driver = Driver(**driver_in.model_dump())
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


async def get_driver_by_id(db: AsyncSession, driver_id: int) -> Driver | None:
    """Возвращает водителя по primary key."""
    return await db.get(Driver, driver_id)


async def get_driver_by_phone(db: AsyncSession, phone: str) -> Driver | None:
    """Возвращает водителя по телефону (с нормализацией)."""
    stmt = select(Driver).where(Driver.phone == normalize_phone(phone))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_drivers(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    search: str | None = None,
) -> list[Driver]:
    """Возвращает страницу водителей с фильтрами по статусу и поиску."""
    stmt = (
        select(Driver)
        .order_by(Driver.last_name, Driver.first_name)
        .offset(skip)
        .limit(limit)
    )
    if status is not None:
        stmt = stmt.where(Driver.status == status)
    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Driver.last_name.ilike(pattern),
                Driver.first_name.ilike(pattern),
                Driver.middle_name.ilike(pattern),
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_driver(
    db: AsyncSession,
    driver: Driver,
    driver_in: DriverUpdate,
) -> Driver:
    """Частично обновляет водителя по PATCH семантике."""
    update_data = driver_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)
    await db.commit()
    await db.refresh(driver)
    return driver
