from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Location(Base):
    """Локация — место, куда едем: карьер, объект, РБУ, база."""

    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_locations_status",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_locations_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_locations_longitude",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Название: Карьер Первомайский, Объект на Ленина 5.",
    )
    location_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment=(
            "Тип: base, quarry, rbu, dump, landfill, "
            "construction_site, warehouse, other."
        ),
    )
    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Адрес (свободный текст).",
    )
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="Широта. NULL — не задана.",
    )
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="Долгота. NULL — не задана.",
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
            f"<Location(id={self.id}, name={self.name!r}, type={self.location_type})>"
        )
