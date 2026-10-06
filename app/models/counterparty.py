from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Counterparty(Base):
    """Контрагент — организация или ИП, с которыми ведем расчеты."""

    __tablename__ = "counterparties"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_counterparties_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Название: ООО Кубань Капитал групп, РБУ Юг-Бетон.",
    )
    counterparty_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment=(
            "Тип: rbu, client, fuel_station, service_station, "
            "leasing, contractor, supplier, other."
        ),
    )
    inn: Mapped[str | None] = mapped_column(
        String(12),
        nullable=True,
        comment="ИНН: 10 цифр (юрлицо) или 12 (ИП/физлицо).",
    )
    kpp: Mapped[str | None] = mapped_column(
        String(9),
        nullable=True,
        comment="КПП: 9 цифр.",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Телефон в формате +7XXXXXXXXXX.",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email.",
    )
    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Юридический адрес (свободный текст).",
    )
    contact_person: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Контактное лицо: ФИО, должность.",
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
            f"<Counterparty(id={self.id}, name={self.name!r}, "
            f"type={self.counterparty_type})>"
        )
