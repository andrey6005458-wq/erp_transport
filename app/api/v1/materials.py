from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.material import (
    create_material,
    get_material_by_id,
    list_materials,
    update_material,
)
from app.database.session import session_getter
from app.models.material import Material
from app.schemas.common import RecordId
from app.schemas.material import MaterialCreate, MaterialRead, MaterialUpdate

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/", response_model=MaterialRead, status_code=201)
async def create_material_endpoint(
    material_in: MaterialCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Material:
    """Создать материал."""
    try:
        material = await create_material(db, material_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Материал с таким названием уже существует.",
        ) from err
    return material


@router.get("/", response_model=list[MaterialRead])
async def list_materials_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    material_type: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Material]:
    """Список материалов с фильтрами."""
    return await list_materials(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        material_type=material_type,
        search=search,
    )


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material_endpoint(
    material_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Material:
    """Получить материал по id."""
    material = await get_material_by_id(db, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Материал с id={material_id} не найден",
        )
    return material


@router.patch("/{material_id}", response_model=MaterialRead)
async def update_material_endpoint(
    material_id: RecordId,
    material_in: MaterialUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Material:
    """Обновить материал (PATCH семантика)."""
    material = await get_material_by_id(db, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Материал с id={material_id} не найден",
        )
    try:
        material = await update_material(db, material, material_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Материал с таким названием уже существует",
        ) from err
    return material
