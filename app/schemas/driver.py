"""Pydantic-схемы для водителей."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.phone import normalize_phone

_PHONE_VALID = re.compile(r"^(\+7|8)\d{10}$")


class DriverBase(BaseModel):
    """Общие поля водителя для Create/Read/Update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="Фамилия.",
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="Имя.",
    )
    middle_name: str | None = Field(
        default=None,
        max_length=100,
        description="Отчество. Может отсутствовать.",
    )
    phone: str = Field(
        max_length=20,
        description=(
            "Телефон в формате +7XXXXXXXXXX. Допускается 8XXXXXXXXXX, "
            "пробелы, скобки, дефисы."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Свободные заметки.",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Проверить телефон, привести к +7XXXXXXXXXX."""
        cleaned = normalize_phone(value)
        if not _PHONE_VALID.match(cleaned):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX "
                "(допускаются пробелы, скобки, дефисы)."
            )
        return cleaned


class DriverCreate(DriverBase):
    """Схема создания водителя."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "last_name": "Иванов",
                "first_name": "Иван",
                "middle_name": "Иванович",
                "phone": "+79001234567",
                "notes": "Категория CE, опыт 10 лет",
            }
        },
    )


class DriverRead(DriverBase):
    """Схема чтения водителя."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "last_name": "Иванов",
                "first_name": "Иван",
                "middle_name": "Иванович",
                "phone": "+79001234567",
                "status": "active",
                "notes": "Категория CE, опыт 10 лет",
                "created_at": "2026-10-03T10:00:00+03:00",
                "updated_at": "2026-10-03T10:00:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    status: Literal["active", "fired"] = Field(description="Жизненный цикл.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class DriverUpdate(BaseModel):
    """Схема обновления водителя. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    status: Literal["active", "fired"] | None = Field(default=None)
    notes: str | None = Field(default=None)

    @field_validator("phone")
    @classmethod
    def validate_phone_update(cls, value: str | None) -> str | None:
        """Проверить телефон, если он передан."""
        if value is None:
            return value
        cleaned = normalize_phone(value)
        if not _PHONE_VALID.match(cleaned):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX "
                "(допускаются пробелы, скобки, дефисы)."
            )
        return cleaned
