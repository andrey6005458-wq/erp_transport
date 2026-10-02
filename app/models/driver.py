from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.driver_absence import DriverAbsence

DRIVER_STATUR = (
    "active",  # работает
    "fired",  # уволен
)


class Driver(Base):
    """Водитель или машинист спецтехники."""

    __tablename__ = "drivers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Фамилия.",
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Имя.")
    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        comment="Отчество. Может отсутствовать.",
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="Телефон в формате +7ХХХХХХХХХХ. Хранится нормализованным.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
        comment="Жизненный цикл: active, fired. Отпуска — в driver_absences.",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Свободные заметки.",
    )
    сreated_at: Mapped[datetime] = mapped_column(
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

    absences: Mapped[list["DriverAbsence"]] = relationship(
        back_populates="driver",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("status IN ('active', 'fired')", name="ck_drivers_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Driver(id={self.id}, last_name={self.last_name!r}, "
            f"phone={self.phone!r}, status={self.status!r})>"
        )
