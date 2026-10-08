from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_location_returns_201(client: AsyncClient) -> None:
    """POST создает локацию."""
    payload = {
        "name": "Карьер Шархинский",
        "location_type": "quarry",
        "address": "село Малый Маяк, территория Промышленная зона, 3",
        "latitude": "44.611612",
        "longitude": "34.344047",
        "notes": "Нерудные строительные материалы",
    }

    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Карьер Шархинский"
    assert data["location_type"] == "quarry"
    assert data["latitude"] == "44.611612"
    assert data["longitude"] == "34.344047"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


async def test_create_location_minimal(client: AsyncClient) -> None:
    """Минимальный набор полей."""
    payload = {"name": "База", "location_type": "base"}

    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["address"] is None
    assert data["latitude"] is None
    assert data["longitude"] is None


async def test_create_location_duplicate_name_returns_409(
    client: AsyncClient, make_location
) -> None:
    """Дубликат name -> 409."""
    await make_location(name="Карьер")

    payload = {"name": "Карьер", "location_type": "quarry"}
    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "название" in detail.lower() or "существует" in detail.lower()


async def test_create_location_invalid_type_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неизвестный location_type -> 422."""
    payload = {"name": "Тест", "location_type": "spaceship"}
    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 422


async def test_create_location_invalid_latitude_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """latitude > 90 → 422."""
    payload = {
        "name": "Тест",
        "location_type": "quarry",
        "latitude": "100.0",
    }
    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 422


async def test_create_location_invalid_longitude_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """longitude > 180 → 422."""
    payload = {
        "name": "Тест",
        "location_type": "quarry",
        "longitude": "200.0",
    }
    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 422


async def test_create_location_empty_name_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустое имя → 422."""
    payload = {"name": "", "location_type": "quarry"}
    response = await client.post("/api/v1/locations/", json=payload)

    assert response.status_code == 422


async def test_list_locations_empty_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/locations/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_locations_returns_200(client: AsyncClient, make_location) -> None:
    """Возвращает все созданные."""
    await make_location(name="А")
    await make_location(name="Б")
    await make_location(name="В")

    response = await client.get("/api/v1/locations/")

    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_list_locations_filter_by_type(
    client: AsyncClient, make_location
) -> None:
    """?location_type=quarry фильтрует."""
    await make_location(location_type="quarry")
    await make_location(location_type="quarry")
    await make_location(location_type="dump")

    response = await client.get("/api/v1/locations/?location_type=quarry")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(loc["location_type"] == "quarry" for loc in data)


async def test_list_locations_filter_by_status(
    client: AsyncClient, make_location
) -> None:
    """?status=archived возвращает только архивные."""
    await make_location(status="active")
    await make_location(status="archived")

    response = await client.get("/api/v1/locations/?status=archived")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "archived"


async def test_list_locations_search_by_name(
    client: AsyncClient, make_location
) -> None:
    """?search=Карьер находит по имени."""
    await make_location(name="Карьер Шархинский")
    await make_location(name="Карьер Балаклавский")

    response = await client.get("/api/v1/locations/?search=Балаклавский")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Карьер Балаклавский"


async def test_list_locations_search_by_address(
    client: AsyncClient, make_location
) -> None:
    """?search=Ялта находит по адресу."""
    await make_location(name="Объект 1", address="г. Ялта, ул. Рузвельта")
    await make_location(name="Объект 2", address="г. Алушта, ул. Морская")

    response = await client.get("/api/v1/locations/?search=Ялта")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Ялта" in data[0]["address"]


async def test_list_locations_pagination(client: AsyncClient, make_location) -> None:
    """?skip=1&limit=1 возвращает одну запись."""
    l1 = await make_location(name="А")
    l2 = await make_location(name="Б")
    await make_location(name="В")

    response = await client.get("/api/v1/locations/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == l2.id
    assert l1.id != l2.id


async def test_get_location_by_id_returns_200(
    client: AsyncClient, make_location
) -> None:
    """GET /locations/{id} возвращает локацию."""
    location = await make_location(name="Карьер")

    response = await client.get(f"/api/v1/locations/{location.id}")

    assert response.status_code == 200
    assert response.json()["id"] == location.id


async def test_get_location_by_id_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий id → 404."""
    response = await client.get("/api/v1/locations/999999")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


async def test_get_location_by_id_too_large_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """id > int4 → 422."""
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/locations/{too_large}")

    assert response.status_code == 422


async def test_update_location_returns_200(client: AsyncClient, make_location) -> None:
    """PATCH обновляет локацию."""
    location = await make_location(name="Старое")

    response = await client.patch(
        f"/api/v1/locations/{location.id}",
        json={"name": "Новое"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Новое"


async def test_update_location_status_archived(
    client: AsyncClient, make_location
) -> None:
    """Soft delete через status=archived."""
    location = await make_location(status="active")

    response = await client.patch(
        f"/api/v1/locations/{location.id}",
        json={"status": "archived"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


async def test_update_location_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH несуществующего → 404."""
    response = await client.patch(
        "/api/v1/locations/999999",
        json={"name": "Тест"},
    )

    assert response.status_code == 404


async def test_update_location_duplicate_name_returns_409(
    client: AsyncClient, make_location
) -> None:
    """PATCH на чужое name → 409."""
    await make_location(name="Карьер 1")
    loc2 = await make_location(name="Карьер 2")

    response = await client.patch(
        f"/api/v1/locations/{loc2.id}",
        json={"name": "Карьер 1"},
    )

    assert response.status_code == 409
