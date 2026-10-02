"""Модель периода отсутствия водителя (отпуск, больничный и т.п.)."""

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

ABSENCE_TYPES = (
    "vacation",  # отпуск
    "sick_leave",  # больничный
    "absenteeism",  # прогул
    "other",  # другое
)


class DriverAbsence(Base):
    """Период отсутствия водителя.

    Отпуска и больничные — это интервалы времени, а не состояние карточки.
    date_to = NULL означает, что водитель ещё не вернулся (актуально для больничного).
    """

    __tablename__ = "driver_absences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Водитель, к которому относится отсутствие.",
    )
    absence_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Тип: vacation, sick_leave, absenteeism, other.",
    )
    date_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Дата начала отсутствия.",
    )
    date_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="Дата окончания. NULL — водитель ещё не вернулся.",
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий: причина, детали.",
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

    driver: Mapped["Driver"] = relationship(back_populates="absences")

    __table_args__ = (
        CheckConstraint(
            "absence_type IN ('vacation', 'sick_leave', 'absenteeism', 'other')",
            name="ck_driver_absences_type",
        ),
        CheckConstraint(
            "date_to IS NULL OR date_to >= date_from",
            name="ck_driver_absences_dates",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DriverAbsence(id={self.id}, driver_id={self.driver_id}, "
            f"type={self.absence_type!r}, {self.date_from}..{self.date_to})>"
        )
