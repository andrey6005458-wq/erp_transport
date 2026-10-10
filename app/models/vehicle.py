from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

VEHICLE_TYPES = (
    "dump_truck",  # самосвал
    "manipulator",  # манипулятор
    "excavator",  # экскаватор
    "dropside",  # бортовой автомобиль
    "other",  # другой вид техники
)

VEHICLE_STATUSES = (
    "active",  # работает
    "repair",  # в ремонте
    "sold",  # продана
)


class Vehicle(Base):
    """Единица техники в парке компании."""

    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plate_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Госномер. Хранится в верхнем регистре без пробелов.",
    )
    vin: Mapped[str] = mapped_column(
        String(17),
        unique=True,
        nullable=False,
        comment="VIN. Хранится в верхнем регистре без пробелов.",
    )
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Год выпуска.",
    )
    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Тип техники: dump_truck, manipulator, excavator, dropside, ...",
    )

    capacity_kg: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Грузоподъемность в кг."
    )
    volume_m3: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Объем кузова в м³."
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Свободные заметки."
    )
    fuel_consumption_per_100km: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Расход л/100км. Для колёсной техники.",
    )
    fuel_consumption_per_hour: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Расход л/час. Для спецтехники.",
    )
    has_attachment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Есть навесное оборудование (гидромолот, трамбовка, ямобур).",
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

    __table_args__ = (
        CheckConstraint(
            "vehicle_type IN ("
            "'dump_truck', 'manipulator', 'excavator', 'dropside', 'other'"
            ")",
            name="ck_vehicles_type",
        ),
        CheckConstraint(
            "status IN ('active', 'repair', 'sold')",
            name="ck_vehicles_status",
        ),
        CheckConstraint(
            "year >= 2010 AND year <= 2150",
            name="ck_vehicles_year",
        ),
        CheckConstraint(
            "capacity_kg IS NULL OR capacity_kg > 0",
            name="ck_vehicles_capacity_positive",
        ),
        CheckConstraint(
            "volume_m3 IS NULL OR volume_m3 > 0",
            name="ck_vehicles_volume_positive",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Vehicle(id={self.id}, plate={self.plate_number!r}, "
            f"type={self.vehicle_type!r})>"
        )
