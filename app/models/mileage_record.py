from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.vehicle import Vehicle


class MileageRecord(Base):
    """Показание одометра на дату. История пробега машины."""

    __tablename__ = "mileage_records"
    __table_args__ = (
        CheckConstraint(
            "source IN ('manual', 'trip', 'gps')",
            name="ck_mileage_records_source",
        ),
        CheckConstraint(
            "mileage_km >= 0",
            name="ck_mileage_records_mileage_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Машина.",
    )
    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Дата показания.",
    )
    mileage_km: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Показания одометра, км.",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="manual",
        comment="Источник: manual (водитель), trip (расчёт), gps (трекер).",
    )
    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Кто ввёл (если водитель).",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Свободные заметки.",
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

    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        lazy="selectin",
    )
    driver: Mapped["Driver | None"] = relationship(
        "Driver",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Отладочное представление."""
        return (
            f"<MileageRecord(id={self.id}, vehicle_id={self.vehicle_id}, "
            f"date={self.record_date}, km={self.mileage_km})>"
        )
