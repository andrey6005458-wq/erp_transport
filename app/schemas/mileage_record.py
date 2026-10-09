from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MileageRecordSource = Literal["manual", "trip", "gps"]


class MileageRecordBase(BaseModel):
    """Общие поля записи одометра для Create/Read."""

    model_config = ConfigDict(str_strip_whitespace=True)

    record_date: date = Field(description="Дата показания.")
    mileage_km: int = Field(
        ge=0,
        description="Показания одометра, км.",
    )
    source: MileageRecordSource = Field(
        default="manual",
        description="Источник: manual (водитель), trip (расчёт), gps (трекер).",
    )
    driver_id: int | None = Field(
        default=None,
        description="Кто ввёл (если водитель).",
    )
    notes: str | None = Field(
        default=None,
        description="Свободные заметки.",
    )


class MileageRecordCreate(MileageRecordBase):
    """Схема создания записи одометра."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "record_date": "2026-10-01",
                "mileage_km": 152340,
                "source": "manual",
                "driver_id": 1,
                "notes": "Снял с одометра",
            }
        },
    )


class MileageRecordRead(MileageRecordBase):
    """Схема чтения записи одометра."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "vehicle_id": 1,
                "record_date": "2026-10-01",
                "mileage_km": 152340,
                "source": "manual",
                "driver_id": 1,
                "notes": "Снял с одометра",
                "created_at": "2026-10-01T10:00:00+03:00",
                "updated_at": "2026-10-01T10:00:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    vehicle_id: int = Field(description="ID машины.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class MileageRecordUpdate(BaseModel):
    """Схема обновления записи одометра. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    record_date: date | None = Field(default=None)
    mileage_km: int | None = Field(default=None, ge=0)
    source: MileageRecordSource | None = Field(default=None)
    driver_id: int | None = Field(default=None)
    notes: str | None = Field(default=None)
