from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_vehicle_returns_201(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST создаёт технику и возвращает 201."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
        "capacity_kg": 30000,
        "volume_m3": "20.00",
    }

    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["plate_number"] == "О957АУ"
    assert data["vin"] == "XTA1234567890ABCD"
    assert data["brand"] == "Mercedes"
    assert data["vehicle_type"] == "dump_truck"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_vehicle_normalizes_plate_via_api(
    client: AsyncSession,
    db_session: AsyncSession,
) -> None:
    """plate_number с пробелами и нижним регистром нормализуется."""
    payload = {
        "plate_number": "  о957ау  ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }

    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 201
    assert response.json()["plate_number"] == "О957АУ"


async def test_create_vehicle_duplicate_plate_returns_409(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """Дубликат plate_number -> 409 с сообщением про госномер."""
    await make_vehicle(plate_number="О957АУ", vin="XTA1234567890ABCD")

    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA9999999999ZZZZ",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }
    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "госномер" in detail.lower()


async def test_create_vehicle_duplicate_vin_returns_409(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """Дубликат vin → 409 с сообщением про VIN."""
    await make_vehicle(plate_number="О957АУ", vin="XTA1234567890ABCD")

    payload = {
        "plate_number": "А999БВ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }
    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "vin" in detail.lower()


async def test_create_vehicle_invalid_vin_length_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """VIN короче 17 символов -> 422 от Pydantic."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "SHORT",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "dump_truck",
    }

    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 422


async def test_create_vehicle_invalid_year_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Год < 2010 -> 422 от Pydantic."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 1990,
        "vehicle_type": "dump_truck",
    }

    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 422


async def test_create_vehicle_invalid_type_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Неизвестный vehicle_type -> 422."""
    payload = {
        "plate_number": "О957АУ",
        "vin": "XTA1234567890ABCD",
        "brand": "Mercedes",
        "model": "Arocs",
        "year": 2023,
        "vehicle_type": "spaceship",
    }
    response = await client.post("/api/v1/vehicles/", json=payload)

    assert response.status_code == 422


async def test_get_vehicle_by_id_returns_200(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """GET по id возвращает технику."""
    vehicle = await make_vehicle(plate_number="О957АУ")

    response = await client.get(f"/api/v1/vehicles/{vehicle.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == vehicle.id
    assert data["plate_number"] == "О957АУ"


async def test_get_vehicle_by_id_not_found_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Несуществующий id → 404."""
    response = await client.get("/api/v1/vehicles/999999")

    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


async def test_list_vehicles_returns_200_empty(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/vehicles/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_vehicles_returns_200(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """Возвращает всех созданных."""
    await make_vehicle(plate_number="А001АА")
    await make_vehicle(plate_number="Б002ББ")
    await make_vehicle(plate_number="В003ВВ")

    response = await client.get("/api/v1/vehicles/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


async def test_list_vehicles_filter_by_status(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """?status=repair возвращает только технику в ремонте."""
    await make_vehicle(status="active")
    await make_vehicle(status="active")
    await make_vehicle(status="repair")

    response = await client.get("/api/v1/vehicles/?status=repair")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "repair"


async def test_list_vehicles_pagination(
    client: AsyncClient,
    make_vehicle,
) -> None:
    """?skip=1&limit=1 возвращает одну запись."""
    v1 = await make_vehicle()
    v2 = await make_vehicle()
    await make_vehicle()

    response = await client.get("/api/v1/vehicles/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == v2.id
    assert v1.id != v2.id


async def test_get_vehicle_by_id_too_large_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """id больше int4 (2^31-1) → 422, не 500.

    Postgres INTEGER не принимает значения > 2_147_483_647.
    Без валидации FastAPI прокидывает огромное число в SQL,
    Postgres падает с DataError → 500. Должно быть 422.
    """
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/vehicles/{too_large}")

    assert response.status_code == 422
