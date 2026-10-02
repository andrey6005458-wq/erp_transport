from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VehicleType = Literal[
    "dump_truck",
    "manipulator",
    "excavator",
    "dropside",
    "other",
]

VehicleStatus = Literal["active", "repair", "sold"]


class VehicleBase(BaseModel):
    """Общие поля техники: используется в Create и Read."""

    plate_number: str = Field(
        min_length=5,
        max_length=20,
        description="Госномер. Хранится в верхнем регистре без пробелов.",
    )
    vin: str = Field(
        min_length=17,
        max_length=17,
        description="VIN. Ровно 17 символов.",
    )
    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=2010, le=2150, description="Год выпуска.")
    vehicle_type: VehicleType = Field(description="Тип техники.")
    capacity_kg: int | None = Field(
        default=None, gt=0, description="Грузоподъемность в кг."
    )
    volume_m3: Decimal | None = Field(
        default=None,
        gt=0,
        description="Объем кузова в м³.",
    )
    notes: str | None = Field(
        default=None, max_length=2000, description="Свободные заметки."
    )


class VehicleCreate(VehicleBase):
    """Тело POST /api/v1/vehicles/."""

    status: VehicleStatus = "active"


class VehicleRead(VehicleBase):
    """Тело ответа API. Добавляет id, status, timestamps."""

    id: int
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleUpdate(BaseModel):
    """Тело PATCH /api/v1/vehicles/{id}."""

    plate_number: str | None = Field(
        default=None,
        min_length=5,
        max_length=20,
    )
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    brand: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    year: int | None = Field(default=None, ge=2010, le=2150)
    vehicle_type: VehicleType | None = None
    capacity_kg: int | None = Field(default=None, gt=0)
    volume_m3: Decimal | None = Field(default=None, gt=0)
    status: VehicleStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)
