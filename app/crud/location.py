from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


async def create_location(
    db: AsyncSession,
    location_in: LocationCreate,
) -> Location:
    """Создать локацию."""
    location = Location(**location_in.model_dump())
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


async def get_location_by_id(
    db: AsyncSession,
    location_id: int,
) -> Location | None:
    """Возвращает локацию по primary key."""
    return await db.get(Location, location_id)


async def get_location_by_name(
    db: AsyncSession,
    name: str,
) -> Location | None:
    """Возвращает локацию по имени."""
    stmt = select(Location).where(Location.name == name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_locations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    location_type: str | None = None,
    search: str | None = None,
) -> list[Location]:
    """Возвращает страницу локаций с фильтрами."""
    stmt = select(Location).order_by(Location.name).offset(skip).limit(limit)
    if status is not None:
        stmt = stmt.where(Location.status == status)
    if location_type is not None:
        stmt = stmt.where(Location.location_type == location_type)
    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Location.name.ilike(pattern),
                Location.address.ilike(pattern),
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_location(
    db: AsyncSession,
    location: Location,
    location_in: LocationUpdate,
) -> Location:
    """Частично обновить локацию по PATCH семантике."""
    update_data = location_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    await db.commit()
    await db.refresh(location)
    return location
