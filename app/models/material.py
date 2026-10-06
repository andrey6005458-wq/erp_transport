from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Material(Base):
    """Материал — щебень, бетон, грунт, газоблок и т.д."""

    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_materials_status",
        ),
        CheckConstraint(
            "density_kg_m3 IS NULL OR density_kg_m3 > 0",
            name="ck_materials_density_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Название: Щебень 5-20, Газоблок D500, Дизель.",
    )
    material_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment=(
            "Тип: inert, concrete, soil, construction_waste, msw, "
            "fuel, building_material, other."
        ),
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Единица измерения: ton, m3, piece, liter, pallet, bag, roll.",
    )
    is_bulk: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Насыпной? True — тарификация по массе.",
    )
    density_kg_m3: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Плотность кг/м³. NULL — не задана.",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Свободные заметки.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
        index=True,
        comment="active / archived.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """Отладочное представление."""
        return (
            f"<Material(id={self.id}, name={self.name!r}, type={self.material_type})>"
        )
