from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.mileage_record import (
    create_mileage_record,
    get_latest_mileage_record,
    get_mileage_record_by_id,
    list_mileage_records_by_vehicle,
    update_mileage_record,
)
from app.crud.vehicle import get_vehicle_by_id
from app.database.session import session_getter
from app.models.mileage_record import MileageRecord
from app.schemas.common import RecordId
from app.schemas.mileage_record import (
    MileageRecordCreate,
    MileageRecordRead,
    MileageRecordUpdate,
)

router = APIRouter(
    prefix="/vehicles/{vehicle_id}/mileage-records",
    tags=["mileage-records"],
)


async def _ensure_vehicle_exists(db: AsyncSession, vehicle_id: int) -> None:
    """Проверить, что машина существует, иначе 404."""
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Машина с id={vehicle_id} не найдена",
        )


@router.post("/", response_model=MileageRecordRead, status_code=201)
async def create_mileage_record_endpoint(
    vehicle_id: RecordId,
    record_in: MileageRecordCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> MileageRecord:
    """Создать запись одометра для машин."""
    await _ensure_vehicle_exists(db, vehicle_id)
    return await create_mileage_record(db, vehicle_id, record_in)


@router.get("/", response_model=list[MileageRecordRead])
async def list_mileage_records_endpoint(
    vehicle_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
    skip: int = 0,
    limit: int = 100,
) -> list[MileageRecord]:
    """Список записей одометра маишны (всежие вперед)."""
    await _ensure_vehicle_exists(db, vehicle_id)
    return await list_mileage_records_by_vehicle(
        db, vehicle_id, skip=skip, limit=limit
    )


@router.get("/latest", response_model=MileageRecordRead)
async def get_latest_mileage_record_endpoint(
    vehicle_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> MileageRecord:
    """Последняя (по дате) запись одометра."""
    await _ensure_vehicle_exists(db, vehicle_id)
    record = await get_latest_mileage_record(db, vehicle_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"У машины {vehicle_id} нет записей одометра",
        )
    return record


@router.get("/{record_id}", response_model=MileageRecordRead)
async def get_mileage_record_endpoint(
    vehicle_id: RecordId,
    record_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> MileageRecord:
    """Получить запись одометра по id."""
    record = await get_mileage_record_by_id(db, record_id)
    if record is None or record.vehicle_id != vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запись с id={record_id} у машины {vehicle_id} не найдена",
        )
    return record


@router.patch("/{record_id}", response_model=MileageRecordRead)
async def update_mileage_record_endpoint(
    vehicle_id: RecordId,
    record_id: RecordId,
    record_in: MileageRecordUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> MileageRecord:
    """Обновить запись одометра (PATCH семантика)."""
    record = await get_mileage_record_by_id(db, record_id)
    if record is None or record.vehicle_id != vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запись с id={record_id} у машины {vehicle_id} не найдена",
        )
    return await update_mileage_record(db, record, record_in)


