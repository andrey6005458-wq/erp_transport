from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.driver import DriverShortRead

AbsenceType = Literal["vacation", "sick_leave", "absenteeism", "other"]


class DriverAbsenceBase(BaseModel):
    """Общие поля отсутствия для Create/Read/Update."""

    model_config = ConfigDict(str_strip_whitespace=True)
    absence_type: AbsenceType = Field(
        description=(
            "Тип отсутствия: vacation (отпуск), sick_leave (больничный), "
            "absenteeism (прогул), other (другое)."
        )
    )
    date_from: date = Field(description="Дата начала отсутствия.")
    date_to: date | None = Field(
        default=None,
        description="Дата окончания. NULL — водитель ещё не вернулся.",
    )
    reason: str | None = Field(
        default=None,
        description="Комментарий: причина, детали.",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "DriverAbsenceBase":
        """Проверить, что date_to >= date_from, если date_to задан."""
        if self.date_to is not None and self.date_to < self.date_from:
            raise ValueError("date_to не может быть раньше date_from.")
        return self


class DriverAbsenceCreate(DriverAbsenceBase):
    """Схема создания отсутствия."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "absence_type": "vacation",
                "date_from": "2026-06-01",
                "date_to": "2026-06-14",
                "reason": "Ежегодный оплачиваемый",
            }
        },
    )


class DriverAbsenceRead(DriverAbsenceBase):
    """Схема чтения отсутствия."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "driver_id": 1,
                "driver": {
                    "id": 1,
                    "last_name": "Иванов",
                    "first_name": "Иван",
                    "middle_name": "Иванович",
                },
                "absence_type": "vacation",
                "date_from": "2026-06-01",
                "date_to": "2026-06-14",
                "reason": "Ежегодный оплачиваемый",
                "created_at": "2026-10-03T10:00:00+03:00",
                "updated_at": "2026-10-03T10:00:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    driver_id: int = Field(description="ID водителя.")
    driver: DriverShortRead = Field(description="Краткая информация о водителе.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class DriverAbsenceUpdate(BaseModel):
    """Схема обновления отсутствия. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    absence_type: AbsenceType | None = Field(default=None)
    date_from: date | None = Field(default=None)
    date_to: date | None = Field(default=None)
    reason: str | None = Field(default=None)
