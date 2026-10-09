from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_mileage_record_returns_201(
    client: AsyncClient, make_vehicle
) -> None:
    """POST создаёт запись одометра."""
    vehicle = await make_vehicle()

    payload = {
        "record_date": "2026-10-01",
        "mileage_km": 152340,
        "source": "manual",
        "notes": "Снял с одометра",
    }
    response = await client.post(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["vehicle_id"] == vehicle.id
    assert data["record_date"] == "2026-10-01"
    assert data["mileage_km"] == 152340
    assert data["source"] == "manual"
    assert "id" in data


async def test_create_mileage_record_minimal(
    client: AsyncClient, make_vehicle
) -> None:
    """Минимальный набор."""
    vehicle = await make_vehicle()

    payload = {"record_date": "2026-10-01", "mileage_km": 100000}
    response = await client.post(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "manual"
    assert data["driver_id"] is None


async def test_create_mileage_record_vehicle_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующая машина -> 404."""
    payload = {"record_date": "2026-10-01", "mileage_km": 100000}
    response = await client.post(
        "/api/v1/vehicles/999999/mileage-records/",
        json=payload,
    )

    assert response.status_code == 404


async def test_create_mileage_record_negative_km_returns_422(
    client: AsyncClient, make_vehicle
) -> None:
    """Отрицательный пробег → 422."""
    vehicle = await make_vehicle()

    payload = {"record_date": "2026-10-01", "mileage_km": -100}
    response = await client.post(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/",
        json=payload,
    )

    assert response.status_code == 422


async def test_list_mileage_records_empty_returns_200(
    client: AsyncClient, make_vehicle
) -> None:
    """Нет записей → пустой список."""
    vehicle = await make_vehicle()

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/"
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_list_mileage_records_returns_200(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """Возвращает все записи машины."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle)
    await make_mileage_record(vehicle=vehicle)

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_mileage_records_vehicle_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующая машина → 404."""
    response = await client.get(
        "/api/v1/vehicles/999999/mileage-records/"
    )

    assert response.status_code == 404


async def test_list_mileage_records_ordered_desc(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """Свежие вперёд."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 1, 1))
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 10, 1))

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/"
    )

    data = response.json()
    assert data[0]["record_date"] == "2026-10-01"
    assert data[1]["record_date"] == "2026-01-01"


async def test_get_latest_mileage_record_returns_200(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """Последняя запись."""
    vehicle = await make_vehicle()
    await make_mileage_record(vehicle=vehicle, record_date=date(2026, 1, 1))
    latest = await make_mileage_record(
        vehicle=vehicle, record_date=date(2026, 10, 1)
    )

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/latest"
    )

    assert response.status_code == 200
    assert response.json()["id"] == latest.id


async def test_get_latest_mileage_record_not_found_returns_404(
    client: AsyncClient, make_vehicle
) -> None:
    """Нет записей -> 404."""
    vehicle = await make_vehicle()

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/latest"
    )

    assert response.status_code == 404
    assert "нет записей" in response.json()["detail"].lower()


async def test_get_mileage_record_by_id_returns_200(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """Получение по id."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(vehicle=vehicle)

    response = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/{record.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == record.id


async def test_get_mileage_record_wrong_vehicle_returns_404(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """IDOR: запись принадлежит другой машине → 404."""
    v1 = await make_vehicle()
    v2 = await make_vehicle()
    record = await make_mileage_record(vehicle=v1)

    response = await client.get(
        f"/api/v1/vehicles/{v2.id}/mileage-records/{record.id}"
    )

    assert response.status_code == 404


async def test_update_mileage_record_returns_200(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """PATCH обновляет."""
    vehicle = await make_vehicle()
    record = await make_mileage_record(vehicle=vehicle, mileage_km=100_000)

    response = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/{record.id}",
        json={"mileage_km": 100_500},
    )

    assert response.status_code == 200
    assert response.json()["mileage_km"] == 100_500


async def test_update_mileage_record_not_found_returns_404(
    client: AsyncClient, make_vehicle
) -> None:
    """PATCH несуществующей → 404."""
    vehicle = await make_vehicle()

    response = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}/mileage-records/999999",
        json={"mileage_km": 100_500},
    )

    assert response.status_code == 404


async def test_update_mileage_record_wrong_vehicle_returns_404(
    client: AsyncClient, make_vehicle, make_mileage_record
) -> None:
    """IDOR: PATCH записи другой машины → 404."""
    v1 = await make_vehicle()
    v2 = await make_vehicle()
    record = await make_mileage_record(vehicle=v1)

    response = await client.patch(
        f"/api/v1/vehicles/{v2.id}/mileage-records/{record.id}",
        json={"mileage_km": 200_000},
    )

    assert response.status_code == 404
