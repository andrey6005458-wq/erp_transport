from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_driver_returns_201(client: AsyncClient) -> None:
    """POST создает водителя и возвращает 201."""
    payload = {
        "last_name": "Фомин",
        "first_name": "Дмитрий",
        "middle_name": "Александрович",
        "phone": "+79781234567",
        "notes": "Водитель самосвала",
    }

    response = await client.post("/api/v1/drivers/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["last_name"] == "Фомин"
    assert data["first_name"] == "Дмитрий"
    assert data["phone"] == "+79781234567"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


async def test_create_driver_normalizes_phone_via_api(
    client: AsyncClient,
) -> None:
    """8XXXXXXXXXX через API → +7XXXXXXXXXX."""
    payload = {
        "last_name": "Иванов",
        "first_name": "Иван",
        "phone": "89781234567",
    }

    response = await client.post("/api/v1/drivers/", json=payload)

    assert response.status_code == 201
    assert response.json()["phone"] == "+79781234567"


async def test_create_driver_duplicate_phone_returns_409(
    client: AsyncClient, make_driver
) -> None:
    """Дубликат phone -> 409 с сообщением про телефон."""
    await make_driver(phone="+79781234567")

    payload = {
        "last_name": "Иванов",
        "first_name": "Иван",
        "phone": "+79781234567",
    }
    response = await client.post("/api/v1/drivers/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "телефон" in detail.lower()


async def test_create_driver_invalid_phone_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Невалидный phone -> 422 от Pydantic."""
    payload = {
        "last_name": "Иванов",
        "first_name": "Иван",
        "phone": "12345",
    }

    response = await client.post("/api/v1/drivers/", json=payload)

    assert response.status_code == 422


async def test_create_driver_empty_last_name_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая фамилия -> 422."""
    payload = {
        "last_name": "",
        "first_name": "Иван",
        "phone": "+79781234567",
    }

    response = await client.post("/api/v1/drivers/", json=payload)

    assert response.status_code == 422


async def test_list_drivers_empty_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/drivers/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_drivers_returns_200(client: AsyncClient, make_driver) -> None:
    """Возвращает всех созданных."""
    await make_driver()
    await make_driver()
    await make_driver()

    response = await client.get("/api/v1/drivers/")

    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_list_drivers_filter_by_status(client: AsyncClient, make_driver) -> None:
    """?status=fired возвращает только уволенных."""
    await make_driver(status="active")
    await make_driver(status="active")
    await make_driver(status="fired")

    response = await client.get("/api/v1/drivers/?status=fired")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "fired"


async def test_list_drivers_search_by_last_name(
    client: AsyncClient, make_driver
) -> None:
    """?search=Фом находится по фамилии."""
    await make_driver(last_name="Фомин", first_name="Дмитрий")
    await make_driver(last_name="Иванов", first_name="Иван")

    response = await client.get("/api/v1/drivers/?search=Фом")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["last_name"] == "Фомин"


async def test_list_drivers_pagination(client: AsyncClient, make_driver) -> None:
    """?skip=1&limit=1 возвращает одну запись."""
    d1 = await make_driver()
    d2 = await make_driver()
    await make_driver()

    response = await client.get("/api/v1/drivers/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == d2.id
    assert d1.id != d2.id


async def test_get_driver_by_phone_returns_200(
    client: AsyncClient, make_driver
) -> None:
    """GET /phone/{phone} находит водителя."""
    driver = await make_driver(phone="+79781234567")

    response = await client.get("/api/v1/drivers/phone/+79781234567")

    assert response.status_code == 200
    assert response.json()["id"] == driver.id


async def test_get_driver_by_phone_normalizes_input(
    client: AsyncClient, make_driver
) -> None:
    """GET /phone/8XXXXXXXXXX находит +7XXXXXXXXXX."""
    driver = await make_driver(phone="+79781234567")

    response = await client.get("/api/v1/drivers/phone/89781234567")

    assert response.status_code == 200
    assert response.json()["id"] == driver.id


async def test_get_driver_by_phone_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий телефон -> 404."""
    response = await client.get("/api/v1/drivers/phone/+79999999999")

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


async def test_list_current_absences_empty_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/drivers/current-absences")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_current_absences_returns_with_driver(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Текущие отсутствия содержат вложенный driver (регрессия)."""
    from datetime import date

    driver = await make_driver(last_name="Фомин")
    await make_absence(driver=driver, date_from=date.today(), date_to=None)

    response = await client.get("/api/v1/drivers/current-absences")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "driver" in data[0]
    assert data[0]["driver"]["last_name"] == "Фомин"
    assert data[0]["driver_id"] == driver.id


async def test_get_driver_by_id_returns_200(client: AsyncClient, make_driver) -> None:
    """GET /drivers/{id} возвращает водителя."""
    driver = await make_driver(last_name="Фомин")

    response = await client.get(f"/api/v1/drivers/{driver.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == driver.id
    assert data["last_name"] == "Фомин"


async def test_get_driver_by_id_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий id -> 404."""
    response = await client.get("/api/v1/drivers/999999")

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


async def test_get_driver_by_id_too_large_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """id > int4 -> 422, а не 500."""
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/drivers/{too_large}")

    assert response.status_code == 422


async def test_update_driver_returns_200(client: AsyncClient, make_driver) -> None:
    """PATCH обновляет водителя."""
    driver = await make_driver(last_name="Иванов")

    response = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"last_name": "Фомин"},
    )

    assert response.status_code == 200
    assert response.json()["last_name"] == "Фомин"


async def test_update_driver_phone_normalized(client: AsyncClient, make_driver) -> None:
    """phone нормализуется при PATCH."""
    driver = await make_driver(phone="+79781234567")

    response = await client.patch(
        f"/api/v1/drivers/{driver.id}",
        json={"pnone": "8 (978) 123-45-67"},
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "+79781234567"


async def test_update_driver_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH несуществующего -> 404."""
    response = await client.patch(
        "/api/v1/drivers/999999",
        json={"last_name": "Фомин"},
    )

    assert response.status_code == 404


async def test_update_driver_duplicate_phone_returns_409(
    client: AsyncClient, make_driver
) -> None:
    """PATCH на чужой phone -> 409."""
    await make_driver(phone="+79781111111")
    driver2 = await make_driver(phone="+79782222222")

    response = await client.patch(
        f"/api/v1/drivers/{driver2.id}",
        json={"phone": "+79781111111"},
    )

    assert response.status_code == 409
