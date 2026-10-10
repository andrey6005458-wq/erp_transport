from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Holiday(Base):
    """Праздничный день. Используется для applies_on='holiday'."""

    __tablename__ = "holidays"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_holidays_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
        comment="Дата праздника.",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Название: Новый год, 8 марта, ...",
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
        return f"<Holiday(id={self.id}, date={self.date}, name={self.name!r})>"
