from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.location import (
    create_location,
    get_location_by_id,
    list_locations,
    update_location,
)
from app.database.session import session_getter
from app.models.location import Location
from app.schemas.common import RecordId
from app.schemas.location import (
    LocationCreate,
    LocationRead,
    LocationUpdate,
)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationRead, status_code=201)
async def create_location_endpoint(
    location_in: LocationCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Location:
    """Создать локацию."""
    try:
        location = await create_location(db, location_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Локация с таким названием уже существует",
        ) from err
    return location


@router.get("/", response_model=list[LocationRead])
async def list_locations_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    location_type: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Location]:
    """Список локаций с фильтрами."""
    return await list_locations(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        location_type=location_type,
        search=search,
    )


@router.get("/{location_id}", response_model=LocationRead)
async def get_location_endpoint(
    location_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Location:
    """Получить локацию по id."""
    location = await get_location_by_id(db, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Локация с id={location_id} не найдена",
        )
    return location


@router.patch("/{location_id}", response_model=LocationRead)
async def update_location_endpoint(
    location_id: RecordId,
    location_in: LocationUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Location:
    """Обновить локацию (PATCH семантика)."""
    location = await get_location_by_id(db, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Локация с id={location_id} не найдена",
        )
    try:
        location = await update_location(db, location, location_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Локация с таким названием уже существует",
        ) from err
    return location
