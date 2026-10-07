import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.phone import normalize_phone

CounterpartyType = Literal[
    "rbu",  # РБУ (бетонный узел)
    "client",  # Клиент
    "fuel_station",  # АЗС
    "service_station",  # СТО (ремонт техники)
    "leasing",  # Лизинговая компания
    "contractor",  # Подрядчик
    "supplier",  # Поставщик ТМЦ
    "other",  # Прочее
]


CounterpartyStatus = Literal["active", "archived"]

_INN_PATTERN = re.compile(r"^(\d{10}|\d{12})$")
_KPP_PATTERN = re.compile(r"^\d{9}$")
_PHONE_PATTERN = re.compile(r"^\+7\d{10}$")


class CounterpartyBase(BaseModel):
    """Общие поля контрагента для Create/Read/Update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Название: ООО Кубань Капитал групп, РБУ Юг-Бетон.",
    )
    counterparty_type: CounterpartyType = Field(
        description=(
            "Тип: rbu, client, fuel_station, service_station, "
            "leasing, contractor, supplier, other."
        )
    )
    inn: str | None = Field(
        default=None,
        description="ИНН: 10 цифр (юрлицо) или 12 (ИП/физлицо).",
    )
    kpp: str | None = Field(
        default=None,
        description="КПП: 9 цифр. У ИП/физлиц отсутствует.",
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Телефон в формате +7XXXXXXXXXX.",
    )
    email: EmailStr | None = Field(
        default=None,
        description="Email.",
    )
    address: str | None = Field(
        default=None,
        max_length=500,
        description="Юридический адрес (свободный текст).",
    )
    contact_person: str | None = Field(
        default=None,
        max_length=200,
        description="Контактное лицо: ФИО, должность.",
    )
    notes: str | None = Field(
        default=None,
        description="Своьодные заметки.",
    )

    @field_validator("inn")
    @classmethod
    def validate_inn(cls, value: str | None) -> str | None:
        """Проверить формат ИНН (10 или 12 цифр)."""
        if value is None:
            return None
        if not _INN_PATTERN.match(value):
            raise ValueError(
                "ИНН должен содержать 10 цифр (юрлицо) или 12 (ИП/физлицо)."
            )
        return value

    @field_validator("kpp")
    @classmethod
    def validate_kpp(cls, value: str | None) -> str | None:
        """Проверить формат КПП (9 цифр)."""
        if value is None:
            return None
        if not _KPP_PATTERN.match(value):
            raise ValueError("КПП должен содержать 9 цифр.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Нормализовать телефон к +7XXXXXXXXXX."""
        if value is None:
            return None
        cleaned = normalize_phone(value)
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX "
                "(допускаются пробелы, скобки, дефисы)."
            )
        return cleaned


class CounterpartyCreate(CounterpartyBase):
    """Схема создания контрагента."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "ООО Кубань Капитал групп",
                "counterparty_type": "client",
                "inn": "2310123456",
                "kpp": "231001001",
                "phone": "+79001234567",
                "email": "info@kuban-kapital.ru",
                "address": "г. Краснодар, ул. Промышленная, 5",
                "contact_person": "Иванов Иван, менеджер",
                "notes": "Отсрочка 30 дней",
            }
        },
    )


class CounterpartyShortRead(BaseModel):
    """Краткая информация о контрагенте для вложенных ответов."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор.")
    name: str = Field(description="Название.")
    counterparty_type: CounterpartyType = Field(description="Тип.")


class CounterpartyRead(CounterpartyBase):
    """Схема чтения контрагента."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "ООО Кубань Капитал групп",
                "counterparty_type": "client",
                "inn": "2310123456",
                "kpp": "231001001",
                "phone": "+79001234567",
                "email": "info@kuban-kapital.ru",
                "address": "г. Краснодар, ул. Промышленная, 5",
                "contact_person": "Иванов Иван, менеджер",
                "notes": "Отсрочка 30 дней",
                "status": "active",
                "created_at": "2026-10-06T10:00:00+03:00",
                "updated_at": "2026-10-06T10:00:00+03:00",
            }
        },
    )

    id: int = Field(description="Идентификатор.")
    status: CounterpartyStatus = Field(description="active / archived.")
    created_at: datetime = Field(description="Дата создания.")
    updated_at: datetime = Field(description="Дата обновления.")


class CounterpartyUpdate(BaseModel):
    """Схема обновления контрагента. Все поля опциональны."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    counterparty_type: CounterpartyType | None = Field(default=None)
    inn: str | None = Field(default=None)
    kpp: str | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    contact_person: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None)
    status: CounterpartyStatus | None = Field(default=None)

    @field_validator("inn")
    @classmethod
    def validate_inn(cls, value: str | None) -> str | None:
        """Проверить формат ИНН, если передан."""
        if value is None:
            return None
        if not _INN_PATTERN.match(value):
            raise ValueError(
                "ИНН должен содержать 10 цифр (юрлицо) или 12 (ИП/физлицо)."
            )
        return value

    @field_validator("kpp")
    @classmethod
    def validate_kpp(cls, value: str | None) -> str | None:
        """Проверить формат КПП, если передан."""
        if value is None:
            return None
        if not _KPP_PATTERN.match(value):
            raise ValueError("КПП должен содержать 9 цифр.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Нормализовать телефон, если передан."""
        if value is None:
            return None
        cleaned = normalize_phone(value)
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX "
                "(допускаются пробелы, скобки, дефисы)."
            )
        return cleaned
