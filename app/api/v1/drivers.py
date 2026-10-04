from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.driver import (
    create_driver,
    get_driver_by_id,
    get_driver_by_phone,
    list_drivers,
    update_driver,
)
from app.crud.driver_absence import list_current_absences
from app.database.session import session_getter
from app.models.driver import Driver
from app.models.driver_absence import DriverAbsence
from app.schemas.common import RecordId
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate
from app.schemas.driver_absence import DriverAbsenceRead

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _parse_unique_violation(err: IntegrityError) -> str:
    """Разбивает IntegrityError на предмет дубликата phone."""
    error_text = str(err.orig).lower()
    if "(phone)" in error_text:
        return "Водитель с таким телефоном уже существует"
    return "Конфликт уникальности данных"


@router.post("/", response_model=DriverRead, status_code=201)
async def create_driver_endpoint(
    driver_in: DriverCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Driver:
    """Создать водителя."""
    try:
        driver = await create_driver(db, driver_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_parse_unique_violation(err),
        ) from err
    return driver


@router.get("/", response_model=list[DriverRead])
async def list_drivers_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Driver]:
    """Список водителей с фильтром по статусу и поиском по ФИО."""
    return await list_drivers(
        db, skip=skip, limit=limit, status=status_filter, search=search
    )


@router.get("/phone/{phone}", response_model=DriverRead)
async def get_driver_by_phone_endpoint(
    phone: str,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Driver:
    """Найти водителя по телефону (для Telegram-бота)."""
    driver = await get_driver_by_phone(db, phone)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Водитель с телефоном {phone} не найден",
        )
    return driver


@router.get("/current-absences", response_model=list[DriverAbsenceRead])
async def list_current_absences_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> list[DriverAbsence]:
    """Список всех отсутствий, активных на текущую дату."""
    return await list_current_absences(db)


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver_endpoint(
    driver_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Driver:
    """Получить водителя по id."""
    driver = await get_driver_by_id(db, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Водитель с id={driver_id} не найден",
        )
    return driver


@router.patch("/{driver_id}", response_model=DriverRead)
async def update_driver_endpoint(
    driver_id: RecordId,
    driver_in: DriverUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Driver:
    """Обновить водителя (PATCH семантика)."""
    driver = await get_driver_by_id(db, driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Водитель с id={driver_id} не найден.",
        )
    try:
        driver = await update_driver(db, driver, driver_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_parse_unique_violation(err),
        ) from err
    return driver
