from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user
from app.schemas.user import UserCreate


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
    assert second.status_code == 409
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


async def test_get_user_by_id_returns_200(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/users/{id} возвращает созданного пользователя."""
    created = await create_user(
        db_session,
        UserCreate(
            email="get_by_id@example.com",
            password="secret123",
            phone="79001112233",
        ),
    )

    response = await client.get(f"/api/v1/users/{created.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created.id
    assert data["email"] == "get_by_id@example.com"
    assert data["phone"] == "79001112233"
    assert "hashed_password" not in data


async def test_get_user_by_id_not_found_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET несуществующего id возвращает 404 с осмысленным detail."""
    response = await client.get("/api/v1/users/99999")

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


async def test_get_user_by_id_invalid_type_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/users/abc возвращает 422."""
    response = await client.get("/api/v1/users/abc")

    assert response.status_code == 422


async def test_list_users_returns_200_empty(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/users на пустой БД возвращает пустой список."""
    response = await client.get("/api/v1/users/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_users_returns_200(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/users/ возвращает всех созданных пользователей."""
    for i in range(3):
        await create_user(
            db_session,
            UserCreate(
                email=f"list_{i}@example.com",
                password="secret123",
                phone=None,
            ),
        )

    response = await client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    emails = {u["email"] for u in data}
    assert emails == {"list_0@example.com", "list_1@example.com", "list_2@example.com"}
    for u in data:
        assert "hashed_password" not in u


async def test_list_users_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/users/?skip=1&limit=1 возвращает одного юзера.

    Порядок в CRUD — order_by(User.id), значит skip=1 пропустит
    самого первого созданного, limit=1 вернёт второго.
    """
    users = []
    for i in range(3):
        u = await create_user(
            db_session,
            UserCreate(
                email=f"page_{i}@example.com",
                password="secret123",
                phone=None,
            ),
        )
        users.append(u)

    response = await client.get("/api/v1/users/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == users[1].id


async def test_get_user_by_id_too_large_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """id больше int4 (2^31-1) → 422, не 500.

    Симметрично vehicles-тесту. Защита на границе int4.
    """
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/users/{too_large}")

    assert response.status_code == 422
