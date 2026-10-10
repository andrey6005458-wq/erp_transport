from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Tariff(Base):
    """Тариф — цена за услугу на период."""

    __tablename__ = "tariffs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_tariffs_status",
        ),
        CheckConstraint(
            "value IS NULL OR value > 0",
            name="ck_tariffs_value_positive",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from",
            name="ck_tariffs_dates",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Тип техники: excavator, dump_truck, manipulator, dropside.",
    )
    work_mode: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
        comment=(
            "Режим: regular (ковш), attachment (навесное), "
            "kmu (работа КМУ), delivery (доставка), haul (перевозка)."
        ),
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Единица: hour, ton, m3, trip, fixed.",
    )
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Откуда (NULL = без привязки к маршруту).",
    )
    to_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Куда (NULL = без привязки к маршруту).",
    )
    material_id: Mapped[int | None] = mapped_column(
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True,
        comment="Конкретный материал (NULL = без материала / только доставка).",
    )
    material_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Категория материала: inert, soil, construction_waste, msw.",
    )
    counterparty_id: Mapped[int | None] = mapped_column(
        ForeignKey("counterparties.id", ondelete="SET NULL"),
        nullable=True,
        comment="Клиент (NULL = для всех).",
    )
    applies_on: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="any",
        index=True,
        comment="any, weekday, weekend, holiday.",
    )
    valid_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="С какой даты действует.",
    )
    valid_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="По какую дату (NULL = бессрочно).",
    )
    value: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Цена за единицу. NULL = договорной (вводится вручную).",
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
            f"<Tariff(id={self.id}, vehicle={self.vehicle_type}, "
            f"mode={self.work_mode}, unit={self.unit}, value={self.value})>"
        )
