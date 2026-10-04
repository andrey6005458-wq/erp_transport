from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.driver import get_driver_by_id
from app.crud.driver_absence import (
    create_absence,
    delete_absence,
    get_absence_by_id,
    get_current_absence_by_driver,
    list_absences_by_driver,
    update_absence,
)
from app.database.session import session_getter
from app.models.driver_absence import DriverAbsence
from app.schemas.common import RecordId
from app.schemas.driver_absence import (
    DriverAbsenceCreate,
    DriverAbsenceRead,
    DriverAbsenceUpdate,
)

router = APIRouter(prefix="/drivers/{driver_id}/absences", tags=["driver-absences"])


async def _ensure_driver_exists(db: AsyncSession, driver_id: int) -> None:
    """Проверить, что водитель существует, иначе 404."""
    driver = await get_driver_by_id(db, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Водитель с id={driver_id} не найден",
        )


@router.post("/", response_model=DriverAbsenceRead, status_code=201)
async def create_absence_endpoint(
    driver_id: RecordId,
    absence_in: DriverAbsenceCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> DriverAbsence:
    """Создать период отсутствия для водителя."""
    await _ensure_driver_exists(db, driver_id)
    try:
        absence = await create_absence(db, driver_id, absence_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    return absence


@router.get("/", response_model=list[DriverAbsenceRead])
async def list_absences_endpoint(
    driver_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
    absence_type: Annotated[str | None, Query()] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DriverAbsence]:
    """Список отсутствий водителя c фильтром по типу."""
    await _ensure_driver_exists(db, driver_id)
    return await list_absences_by_driver(
        db, driver_id, skip=skip, limit=limit, absence_type=absence_type
    )


@router.get("/current", response_model=DriverAbsenceRead)
async def get_current_absence_endpoint(
    driver_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> DriverAbsence:
    """Текущее отсутствие водителя (если есть)."""
    await _ensure_driver_exists(db, driver_id)
    absence = await get_current_absence_by_driver(db, driver_id)
    if absence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"У водителя {driver_id} нет текущего отсутствия",
        )
    return absence


@router.get("/{absence_id}", response_model=DriverAbsenceRead)
async def get_absence_endpoint(
    driver_id: RecordId,
    absence_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> DriverAbsence:
    """Получить одно отсутствие водителя."""
    absence = await get_absence_by_id(db, absence_id)
    if absence is None or absence.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Отсутствие с id={absence_id} у водителя {driver_id} не найдено",
        )
    return absence


@router.patch("/{absence_id}", response_model=DriverAbsenceRead)
async def update_absence_endpoint(
    driver_id: RecordId,
    absence_id: RecordId,
    absence_in: DriverAbsenceUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> DriverAbsence:
    """Обновить отсутствие (PATCH семантика)."""
    absence = await get_absence_by_id(db, absence_id)
    if absence is None or absence.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Отсутствие с id={absence_id} у водителя {driver_id} не найдено",
        )
    try:
        absence = await update_absence(db, absence, absence_in)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    return absence


@router.delete("/{absence_id}", status_code=204)
async def delete_absence_endpoint(
    driver_id: RecordId,
    absence_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> None:
    """Удалить отсутствие."""
    absence = await get_absence_by_id(db, absence_id)
    if absence is None or absence.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Отсутствие с id={absence_id} у водителя {driver_id} не найдено",
        )
    await delete_absence(db, absence)
