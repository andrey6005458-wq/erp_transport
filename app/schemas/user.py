from unittest.mock import Base

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Общие поля пользователя."""

    email: EmailStr


class UserCreate(UserBase):
    """Схема для создания пользователя."""
    password: str
    phone: str | None = None


class UserRead(UserBase):
    """Схема для чтения пользователя (ответ API)."""
    model_config = ConfigDict(from_attributes = True)

    id: int
    is_active: bool
    phone: str | None = None


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""
    email: EmailStr | None = None
    password: str | None = None
    phone: str | None = None
    is_active: bool | None = None 
