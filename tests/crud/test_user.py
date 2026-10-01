"""Тесты для app/crud/user.py."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import verify_password
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
)
from app.schemas.user import UserCreate, UserUpdate


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


async def test_create_user_duplicate_email(db_session):
    """create_user падает на дубликате email (UNIQUE constraint).

    IntegrityError — исключение SQLAlchemy на нарушение ограничений БД.
    После него сессия в невалидном состоянии, нужен rollback.
    """
    user_in = UserCreate(email="alice@example.com", password="secret123")

    await create_user(db_session, user_in)

    with pytest.raises(IntegrityError):
        await create_user(db_session, user_in)

    await db_session.rollback()


async def test_get_user_by_id(db_session):
    """get_user_by_id возвращает пользовалетя по id."""
    user_in = UserCreate(email="bob@example.com", password="secret123")

    created = await create_user(db_session, user_in)

    found = await get_user_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.email == "bob@example.com"


async def test_get_user_by_id_not_found(db_session):
    """get_user_by_id возвращает None, если пользователя нет."""
    found = await get_user_by_id(db_session, 99999)

    assert found is None


async def test_get_user_by_email(db_session):
    """get_user_by_email возвращает пользователя по email."""
    user_in = UserCreate(email="bob@example.com", password="secret123")

    created = await create_user(db_session, user_in)

    found = await get_user_by_email(db_session, created.email)

    assert found is not None
    assert found.email == "bob@example.com"


async def test_get_user_by_email_not_found(db_session):
    """get_user_by_email возвращает None, если email не найден."""
    found = await get_user_by_email(db_session, "nobody@example.com")

    assert found is None


async def test_list_users_empty(db_session):
    """list_users возвращает пустой список, если пользователей нет."""
    users = await list_users(db_session)

    assert users == []


async def test_list_users(db_session):
    """list_users возвращает всех пользователей, отсортированных по id."""
    await create_user(
        db_session, UserCreate(email="bob@example.com", password="secret123")
    )
    await create_user(
        db_session, UserCreate(email="kit@example.com", password="secret456")
    )
    await create_user(
        db_session, UserCreate(email="tik@example.com", password="secret789")
    )

    users = await list_users(db_session)

    assert len(users) == 3
    assert [u.email for u in users] == [
        "bob@example.com",
        "kit@example.com",
        "tik@example.com",
    ]


async def test_list_users_pagination(db_session):
    """list_users уважает skip и limit."""
    for i in range(5):
        await create_user(
            db_session,
            UserCreate(email=f"user{i}@example.com", password="secret123"),
        )

    page = await list_users(db_session, skip=1, limit=2)

    assert len(page) == 2
    assert [u.email for u in page] == ["user1@example.com", "user2@example.com"]


async def test_update_user_email(db_session):
    """update_user обновляет email, не трогая остальные поля."""
    user = await create_user(
        db_session,
        UserCreate(
            email="old@example.com",
            password="secret123",
            phone="+79787821815",
        ),
    )
    old_hash = user.hashed_password

    updated = await update_user(
        db_session,
        user,
        UserUpdate(email="new@example.com"),
    )

    assert updated.id == user.id
    assert updated.email == "new@example.com"
    assert updated.phone == "+79787821815"
    assert updated.hashed_password == old_hash


async def test_update_user_phone(db_session):
    """update_user обновляет phone, не трогая остальные поля."""
    user = await create_user(
        db_session,
        UserCreate(
            email="user@example.com", password="secret123", phone="+79787821815"
        ),
    )
    old_hash = user.hashed_password

    updated = await update_user(
        db_session,
        user,
        UserUpdate(phone="+79189861084"),
    )

    assert updated.email == "user@example.com"
    assert updated.phone == "+79189861084"
    assert updated.hashed_password == old_hash


async def test_update_user_password(db_session):
    """update_user перехеширует новый пароль, старый больше не подходит"""
    user = await create_user(
        db_session,
        UserCreate(
            email="user@example.com", phone="+79782234038", password="old_secret"
        ),
    )
    old_hash = user.hashed_password

    updated = await update_user(
        db_session,
        user,
        UserUpdate(password="new_secret"),
    )

    assert updated.hashed_password != old_hash
    assert verify_password("new_secret", updated.hashed_password) is True
    assert updated.email == "user@example.com"
    assert updated.phone == "+79782234038"


async def test_update_user_multiple_fields(db_session):
    """update_user обновляет email, phone и password за один вызов"""
    user = await create_user(
        db_session,
        UserCreate(
            email="old@example.com", phone="+79993334455", password="old_secret"
        ),
    )
    old_hash = user.hashed_password

    updated = await update_user(
        db_session,
        user,
        UserUpdate(
            email="new@example.com", phone="+79782758271", password="new_secret"
        ),
    )

    assert updated.email == "new@example.com"
    assert updated.phone == "+79782758271"
    assert updated.hashed_password != old_hash
    assert verify_password("new_secret", updated.hashed_password) is True
    assert verify_password("old_secret", updated.hashed_password) is False


async def test_update_user_empty_patch(db_session):
    """update_user с пустым UserUpdate() не меняет ничего."""
    user = await create_user(
        db_session,
        UserCreate(
            email="user@example.com",
            phone="+79782234038",
            password="secret123",
        ),
    )
    old_hash = user.hashed_password
    old_id = user.id

    updated = await update_user(db_session, user, UserUpdate())

    assert updated.id == old_id
    assert updated.email == "user@example.com"
    assert updated.phone == "+79782234038"
    assert updated.hashed_password == old_hash
