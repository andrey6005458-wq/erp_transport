from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.counterparty import (
    create_counterparty,
    get_counterparty_by_id,
    list_counterparties,
    update_counterparty,
)
from app.database.session import session_getter
from app.models.counterparty import Counterparty
from app.schemas.common import RecordId
from app.schemas.counterparty import (
    CounterpartyCreate,
    CounterpartyRead,
    CounterpartyUpdate,
)

router = APIRouter(prefix="/counterparties", tags=["counterparties"])


@router.post("/", response_model=CounterpartyRead, status_code=201)
async def create_counterparty_endpoint(
    counterparty_in: CounterpartyCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Counterparty:
    """Создать контрагента."""
    try:
        counterparty = await create_counterparty(db, counterparty_in)
    except IntegrityError as err:
        await db.rollback()
        print("*** DEBUG: rollback OK")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Контрагент с таким названием уже существует",
        ) from err
    return counterparty


@router.get("/", response_model=list[CounterpartyRead])
async def list_counterparties_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    counterparty_type: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Counterparty]:
    """Список контрагентов с фильтрами."""
    return await list_counterparties(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        counterparty_type=counterparty_type,
        search=search,
    )


@router.get("/{counterparty_id}", response_model=CounterpartyRead)
async def get_counterparty_endpoint(
    counterparty_id: RecordId,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Counterparty:
    """Получить контрагента по id."""
    counterparty = await get_counterparty_by_id(db, counterparty_id)
    if counterparty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Контрагент с id={counterparty_id} не найден",
        )
    return counterparty


@router.patch("/{counterparty_id}", response_model=CounterpartyRead)
async def update_counterparty_endpoint(
    counterparty_id: RecordId,
    counterparty_in: CounterpartyUpdate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> Counterparty:
    """Обновить контрагента (PATCH семантика)."""
    counterparty = await get_counterparty_by_id(db, counterparty_id)
    if counterparty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Контрагент с id={counterparty_id} не найден",
        )
    try:
        counterparty = await update_counterparty(db, counterparty, counterparty_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Контрагент с таким названием уже существует",
        ) from err
    return counterparty
