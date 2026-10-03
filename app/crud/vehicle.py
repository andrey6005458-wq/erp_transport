from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def _normalize_plate(plate: str) -> str:
    """Приводит госномер к единому виду: strip + upper."""
    return plate.strip().upper()


def _normalize_vin(vin: str) -> str:
    """Приводит VIN к единому виду: strip + upper."""
    return vin.strip().upper()


async def create_vehicle(db: AsyncSession, vehicle_in: VehicleCreate) -> Vehicle:
    """Создает единицу техники."""
    data = vehicle_in.model_dump()
    data["plate_number"] = _normalize_plate(data["plate_number"])
    data["vin"] = _normalize_vin(data["vin"])
    vehicle = Vehicle(**data)
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def get_vehicle_by_id(db: AsyncSession, vehicle_id: int) -> Vehicle | None:
    """Возвращает технику по primary key."""
    return await db.get(Vehicle, vehicle_id)


async def get_vehicle_by_plate(db: AsyncSession, plate: str) -> Vehicle | None:
    """Возвращает технику по госномеру."""
    stmt = select(Vehicle).where(Vehicle.plate_number == _normalize_plate(plate))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_vehicles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
) -> list[Vehicle]:
    """Возвращает страницу техники, отсортированную по id."""
    stmt = select(Vehicle).order_by(Vehicle.id).offset(skip).limit(limit)
    if status is not None:
        stmt = stmt.where(Vehicle.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_vehicle(
    db: AsyncSession,
    vehicle: Vehicle,
    vehicle_in: VehicleUpdate,
) -> Vehicle:
    """Частично обновляет технику по PATCH семантике."""
    update_data = vehicle_in.model_dump(exclude_unset=True)

    if update_data.get("plate_number") is not None:
        update_data["plate_number"] = _normalize_plate(update_data["plate_number"])

    if update_data.get("vin") is not None:
        update_data["vin"] = _normalize_vin(update_data["vin"])

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle
