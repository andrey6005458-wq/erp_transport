"""Тесты для app/crud/user.py."""

from app.core.security import verify_password
from app.crud.user import create_user
from app.schemas.user import UserCreate


async def test_create_user(db_session):
    """create_user создаёт пользователя с хешированным паролем."""
    user_in = UserCreate(
        email="alice@example.com",
        password="secret123",
        phone="+79990001122",
    )

    user = await create_user(db_session, user_in)

    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.phone == "+79990001122"
    assert user.hashed_password != "secret123"
    assert verify_password("secret123", user.hashed_password) is True
    assert user.is_active is True
