from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.vehicle import (
    create_vehicle,
    get_vehicle_by_id,
    list_vehicles,
)
from app.database.session import session_getter
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleStatus

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _parse_unique_violation(err: IntegrityError) -> str:
    """Определяет, какой unique constraint нарушен."""
    error_text = str(err.orig)

    if "ix_vehicles_plate_number" in error_text:
        return "Машина с таким госномером уже существует"
    if "vehicle_vin_key" in error_text:
        return "Машина с таким VIN уже существует"
    return "Конфликт уникальности данных"


@router.post("/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle_endpoint(
    vehicle_in: VehicleCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Vehicle:
    """Создает единицу техники."""
    try:
        vehicle = await create_vehicle(db, vehicle_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_parse_unique_violation(err),
        ) from err
    return vehicle


@router.get("/", response_model=list[VehicleRead])
async def list_vehicles_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    skip: int = 0,
    limit: int = 100,
    status_filter: Annotated[VehicleStatus | None, Query(alias="status")] = None,
) -> list[Vehicle]:
    """Возвращает страницу техники с пагинацией и фильтром."""
    return await list_vehicles(db, skip=skip, limit=limit, status=status_filter)


@router.get("/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle_endpoint(
    vehicle_id: int,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Vehicle:
    """Возвращает технику по id. Если не найдена - 404."""
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Техника с id={vehicle_id} не найдена",
        )
    return vehicle
