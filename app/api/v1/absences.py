from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.driver_absence import (
    list_absences_in_period,
    list_absences_on_date,
)
from app.database.session import session_getter
from app.models.driver_absence import DriverAbsence
from app.schemas.driver_absence import DriverAbsenceRead

router = APIRouter(prefix="/absences", tags=["absences"])


@router.get("/", response_model=list[DriverAbsenceRead])
async def list_absences_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    absence_date: Annotated[date | None, Query(alias="date")] = None,
    period_from: date | None = None,
    period_to: date | None = None,
    driver_id: int | None = None,
    absence_type: Annotated[str | None, Query()] = None,
) -> list[DriverAbsence]:
    """Список отсутствий с фильтрами.

    - `?date=2026-06-01` — кто отсутствовал в этот день
    - `?period_from=2026-01-01&period_to=2026-12-31` — за период
    - Комбинируется с `driver_id` и `absence_type`
    """
    if absence_date is not None:
        return await list_absences_on_date(
            db,
            target_date=absence_date,
            driver_id=driver_id,
            absence_type=absence_type,
        )

    if period_from is not None and period_to is not None:
        return await list_absences_in_period(
            db,
            period_from=period_from,
            period_to=period_to,
            driver_id=driver_id,
            absence_type=absence_type,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Укажите либо ?date=X, либо ?period_from=X&period_to=Y",
    )
