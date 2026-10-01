from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_user_returns_201(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST /api/v1/users/ создает пользователя и возвращает 201."""

    payload = {
        "email": "api_create@example.com",
        "password": "secret123",
        "phone": "+79001234567",
    }

    response = await client.post("/api/v1/users/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


async def test_create_user_duplicate_email_returns_409(
        client: AsyncClient,
        db_session: AsyncSession,
) -> None:
    """POST с существующим email возвращает 409 Colflict."""

    payload = {
        "email": "duplicate@example.com",
        "password": "secret123",
        "phone": None,
    }

    first = await client.post("/api/v1/users/", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/users/", json=payload)
    assert second.status_code ==409
    assert "уже существует" in second.json()["detail"].lower()


async def test_create_user_invalid_email_returns_422(
        client: AsyncClient,
        db_session: AsyncSession,
) -> None:
    """POST с невалидным email возвращает 422 от Pydantic."""

    payload = {
        "email": "not-an-email",
        "password": "secret123",
        "phone": None,
    }

    response = await client.post("/api/v1/users/", json=payload)

    assert response.status_code == 422


async def test_create_user_missing_password_returns_422(
        client: AsyncClient,
        db_session: AsyncSession,
) -> None:
    """POST без поля password возвращает 422."""

    payload = {
        "email": "nopassword@example.com",
        "phone": None,
    }

    response = await client.post("/api/v1/users/", json=payload)

    assert response.status_code == 422



