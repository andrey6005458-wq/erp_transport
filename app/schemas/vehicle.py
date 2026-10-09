"""Pydantic-схемы для Vehicle.

Разделение по назначению:
- VehicleBase — общие поля, не используется напрямую.
- VehicleCreate — тело POST-запроса на создание.
- VehicleRead — тело ответа API.
- VehicleUpdate — тело PATCH-запроса, все поля опциональны.
"""

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
    """Общие поля техники: используются в Create и Read."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plate_number": "О957АУ",
                "vin": "XTA1234567890ABCD",
                "brand": "Mercedes",
                "model": "Arocs",
                "year": 2023,
                "vehicle_type": "dump_truck",
                "capacity_kg": 30000,
                "volume_m3": "20.00",
                "notes": "Свободные заметки",
            },
        },
    )

    plate_number: str = Field(
        min_length=5,
        max_length=20,
        description="Госномер. Хранится в верхнем регистре без пробелов.",
        examples=["О957АУ"],
    )
    vin: str = Field(
        min_length=17,
        max_length=17,
        description="VIN. Ровно 17 символов, верхний регистр.",
        examples=["XTA1234567890ABCD"],
    )
    brand: str = Field(min_length=1, max_length=50, examples=["Mercedes"])
    model: str = Field(min_length=1, max_length=50, examples=["Arocs"])
    year: int = Field(ge=2010, le=2150, description="Год выпуска.", examples=[2023])
    vehicle_type: VehicleType = Field(
        description=(
            "Тип техники. Возможные значения:\n"
            "- `dump_truck` — Самосвал\n"
            "- `manipulator` — Манипулятор бортовой\n"
            "- `excavator` — Экскаватор\n"
            "- `dropside` — Бортовой автомобиль\n"
            "- `other` — Другое"
        ),
        examples=["dump_truck"],
    )
    capacity_kg: int | None = Field(
        default=None,
        gt=0,
        description="Грузоподъёмность в кг.",
        examples=[30000],
    )
    volume_m3: Decimal | None = Field(
        default=None,
        gt=0,
        description="Объём кузова в м³.",
        examples=["20.00"],
    )
    fuel_consumption_per_100km: Decimal | None = Field(
        default=None,
        ge=0,
        description="Расход л/100км. Для колёсной техники.",
    )
    fuel_consumption_per_hour: Decimal | None = Field(
        default=None,
        ge=0,
        description="Расход л/час. Для спецтехники.",
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Свободные заметки.",
    )


class VehicleCreate(VehicleBase):
    """Тело POST /api/v1/vehicles/."""

    status: VehicleStatus = Field(
        default="active",
        description=(
            "Статус техники. Возможные значения:\n"
            "- `active` — Работает\n"
            "- `repair` — В ремонте\n"
            "- `sold` — Продана"
        ),
        examples=["active"],
    )


class VehicleRead(VehicleBase):
    """Тело ответа API. Добавляет id, status, timestamps."""

    id: int
    status: VehicleStatus = Field(
        description=(
            "Статус техники:\n"
            "- `active` — Работает\n"
            "- `repair` — В ремонте\n"
            "- `sold` — Продана"
        ),
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleUpdate(BaseModel):
    """Тело PATCH /api/v1/vehicles/{id}."""

    plate_number: str | None = Field(
        default=None,
        min_length=5,
        max_length=20,
        examples=["О957АУ"],
    )
    vin: str | None = Field(
        default=None,
        min_length=17,
        max_length=17,
        examples=["XTA1234567890ABCD"],
    )
    brand: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    year: int | None = Field(default=None, ge=2010, le=2150)
    vehicle_type: VehicleType | None = None
    capacity_kg: int | None = Field(default=None, gt=0)
    volume_m3: Decimal | None = Field(default=None, gt=0)
    status: VehicleStatus | None = None
    fuel_consumption_per_100km: Decimal | None = Field(default=None, ge=0)
    fuel_consumption_per_hour: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)
