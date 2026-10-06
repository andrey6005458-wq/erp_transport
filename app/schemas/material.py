from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MaterialType = Literal[
    "inert",
    "concrete",
    "soil",
    "construction_waste",
    "msw",
    "fuel",
    "building_material",
    "other",
]

MaterialUnit = Literal["ton", "m3", "piece", "liter", "pallet", "bag", "roll"]

MaterialStatus = Literal["active", "archived"]


class MaterialBase(BaseModel):
    """Общие поля материала для Create/Read/Update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Название: Щебень 5-20, Газоблок D500, Дизель.",
    )
    material_type: MaterialType = Field(
        description=(
            "Тип: inert (инертные), concrete (бетон), soil (грунт), "
            "construction_waste (строймусор), msw (ТБО), fuel (топливо), "
            "building_material (стройматериалы), other (прочее)."
        )
    )
    unit: MaterialUnit = Field(
        description="Единица измерения: ton, m3, piece, liter, pallet, bag, roll."
    )
    is_bulk: bool = Field(
        default=False,
        description="Насыпной? True — тарификация по массе.",
    )
    density_kg_m3: int | None = Field(
        default=None,
        gt=0,
        description="Плотность кг/м³. NULL — не задана.",
    )
    notes: str | None = Field(
        default=None,
        description="Свободные заметки.",
    )


class MaterialCreate(MaterialBase):
    """Схема создания материала."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Щебень 5-20",
                "material_type": "inert",
                "unit": "ton",
                "is_bulk": True,
                "density_kg_m3": 1400,
                "notes": "Гранитный, карьер Шархинский",
            }
        },
    )


class MaterialShortRead(BaseModel):
    """Краткая информация о материале для вложенных ответов."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор.")
    name: str = Field(description="Название.")
    unit: MaterialUnit = Field(description="Единица измерения.")


class MaterialRead(MaterialBase):
    """Схема чтения материала."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Щебень 5-20",
                "material_type": "inert",
                "unit": "ton",
                "is_bulk": True,
                "density_kg_m3": 1400,
                "notes": "Гранитный, карьер Шархинский",
                "status": "active",
                "created_at": "2026-10-06T10:00:00+03:00",
                "updated_at": "2026-10-06T10:10:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    status: MaterialStatus = Field(description="active / archived.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class MaterialUpdate(BaseModel):
    """Схема обновления материала. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    material_type: MaterialType | None = Field(default=None)
    unit: MaterialUnit | None = Field(default=None)
    is_bulk: bool | None = Field(default=None)
    density_kg_m3: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None)
    status: MaterialStatus | None = Field(default=None)
