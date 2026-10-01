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
