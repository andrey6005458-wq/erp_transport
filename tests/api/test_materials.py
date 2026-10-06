from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_material_returns_201(client: AsyncClient) -> None:
    """POST создает материал и возвращает 201."""
    payload = {
        "name": "Щебень 5-20",
        "material_type": "inert",
        "unit": "ton",
        "is_bulk": True,
        "density_kg_m3": 1400,
        "notes": "Гранитный",
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Щебень 5-20"
    assert data["material_type"] == "inert"
    assert data["unit"] == "ton"
    assert data["is_bulk"] is True
    assert data["density_kg_m3"] == 1400
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


async def test_create_material_minimal(client: AsyncClient) -> None:
    """Минимальный набор полей."""
    payload = {
        "name": "Газоблок D500",
        "material_type": "building_material",
        "unit": "pallet",
    }

    respons = await client.post("/api/v1/materials/", json=payload)

    assert respons.status_code == 201
    data = respons.json()
    assert data["is_bulk"] is False
    assert data["density_kg_m3"] is None


async def test_create_material_duplicate_name_returns_409(
    client: AsyncClient, make_material
) -> None:
    """Дубликат name -> 409."""
    await make_material(name="Щебень 5-20")

    payload = {
        "name": "Щебень 5-20",
        "material_type": "inert",
        "unit": "ton",
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "название" in detail.lower() or "существует" in detail.lower()


async def test_create_material_invalid_type_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неизвестный material_type -> 422."""
    payload = {
        "name": "Тест",
        "material_type": "spaceship",
        "unit": "ton",
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 422


async def test_create_material_invalid_unit_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неизвестный unit -> 422."""
    payload = {
        "name": "Тест",
        "material_type": "inert",
        "unit": "kg",
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 422


async def test_create_material_invalid_density_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """density_kg_m3 <= 0 → 422."""
    payload = {
        "name": "Тест",
        "material_type": "inert",
        "unit": "ton",
        "density_kg_m3": 0,
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 422


async def test_create_material_empty_name_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустое имя -> 422."""
    payload = {
        "name": "",
        "material_type": "inert",
        "unit": "ton",
    }

    response = await client.post("/api/v1/materials/", json=payload)

    assert response.status_code == 422


async def test_list_materials_empty_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/materials/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_materials_returns_200(client: AsyncClient, make_material) -> None:
    """Возвращает все возданные."""
    await make_material(name="А")
    await make_material(name="Б")
    await make_material(name="В")

    response = await client.get("/api/v1/materials/")

    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_list_materials_filter_by_type(
    client: AsyncClient, make_material
) -> None:
    """?material_type=inert фильтрует."""
    await make_material(material_type="inert")
    await make_material(material_type="inert")
    await make_material(material_type="concrete")

    response = await client.get("/api/v1/materials/?material_type=inert")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(m["material_type"] == "inert" for m in data)


async def test_list_materials_filter_by_status(
    client: AsyncClient, make_material
) -> None:
    """?status=archived возвращает только архивные."""
    await make_material(status="active")
    await make_material(status="archived")

    response = await client.get("/api/v1/materials/?status=archived")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "archived"


async def test_list_materials_search(client: AsyncClient, make_material) -> None:
    """?search=Щебень находит по name."""
    await make_material(name="Щебень 5-20")
    await make_material(name="Песок карьерный")

    response = await client.get("/api/v1/materials/?search=Щебень")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Щебень 5-20"


async def test_list_materials_pagination(client: AsyncClient, make_material) -> None:
    """?skip=1&limit=1 возвращает одну запись."""
    m1 = await make_material(name="А")
    m2 = await make_material(name="Б")
    await make_material(name="В")

    response = await client.get("/api/v1/materials/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == m2.id
    assert m1.id != m2.id


async def test_get_material_by_id_returns_200(
    client: AsyncClient, make_material
) -> None:
    """GET /materials/{id} возвращает материал."""
    material = await make_material(name="Щебень 5-20")

    response = await client.get(f"/api/v1/materials/{material.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == material.id
    assert data["name"] == "Щебень 5-20"


async def test_get_material_by_id_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий id -> 404."""
    response = await client.get("/api/v1/materials/999999")

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


async def test_get_material_by_id_too_large_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """id > int4 -> 422."""
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/materials/{too_large}")

    assert response.status_code == 422


async def test_update_material_returns_200(client: AsyncClient, make_material) -> None:
    """PATCH обновляет материал."""
    material = await make_material(name="Щебень")

    response = await client.patch(
        f"/api/v1/materials/{material.id}",
        json={"name": "Щебень 5-20"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Щебень 5-20"


async def test_update_material_status_archived(
    client: AsyncClient, make_material
) -> None:
    """Soft delete через status=archived."""
    material = await make_material(status="active")

    response = await client.patch(
        f"/api/v1/materials/{material.id}",
        json={"status": "archived"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


async def test_update_material_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH несуществующего -> 404."""
    response = await client.patch(
        "/api/v1/materials/999999",
        json={"name": "Тест"},
    )

    assert response.status_code == 404


async def test_update_material_duplicate_name_returns_409(
    client: AsyncClient, make_material
) -> None:
    """PATCH на чужое name -> 409"""
    await make_material(name="Щебень")
    material2 = await make_material(name="Песок")

    response = await client.patch(
        f"/api/v1/materials/{material2.id}",
        json={"name": "Щебень"},
    )

    assert response.status_code == 409
