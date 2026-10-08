from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LocationType = Literal[
    "base",  # База (стоянка техники)
    "quarry",  # Карьер
    "rbu",  # РБУ
    "dump",  # Отвал (грунт, строймусор)
    "landfill",  # Полигон ТБО
    "construction_site",  # Объект / стройка
    "warehouse",  # Склад
    "other",  # Прочее
]

LocationStatus = Literal["active", "archived"]


class LocationBase(BaseModel):
    """Общие поля локации для Create/Read/Update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Название: Карьер Шархинский. Адрес: г. Алушта, с. Запрудное.",
    )
    location_type: LocationType = Field(
        description=(
            "Тип: base, quarry, rbu, dump, landfill, "
            "construction_site, warehouse, other."
        )
    )
    address: str | None = Field(
        default=None,
        max_length=500,
        description="Адрес (свободный текст).",
    )
    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
        description="Широта: от -90 до 90.",
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
        description="Долгота: от -180 до 180.",
    )
    notes: str | None = Field(
        default=None,
        description="Свободные заметки.",
    )


class LocationCreate(LocationBase):
    """Схема создания локации."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Карьер Первомайский",
                "location_type": "quarry",
                "address": "Симферопольский р-н, с. Первомайское",
                "latitude": "45.1234567",
                "longitude": "34.5678901",
                "notes": "Щебень, песок, ПГС",
            }
        },
    )


class LocationShortRead(BaseModel):
    """Краткая информация о локации для вложенных ответов."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор.")
    name: str = Field(description="Название.")
    location_type: LocationType = Field(description="Тип.")


class LocationRead(LocationBase):
    """Схема чтения локации."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Карьер Первомайский",
                "location_type": "quarry",
                "address": "Симферопольский р-н, с. Первомайское",
                "latitude": "45.1234567",
                "longitude": "34.5678901",
                "notes": "Щебень, песок, ПГС",
                "status": "active",
                "created_at": "2026-10-07T10:00:00+03:00",
                "updated_at": "2026-10-07T10:00:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    status: LocationStatus = Field(description="active / archived.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class LocationUpdate(BaseModel):
    """Схема обновления локации. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    location_type: LocationType | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )
    notes: str | None = Field(default=None)
    status: LocationStatus | None = Field(default=None)
