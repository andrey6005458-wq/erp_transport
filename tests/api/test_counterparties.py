from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_counterparty_returns_201(client: AsyncClient) -> None:
    """POST создает контрагента."""
    payload = {
        "name": "ООО Кубань Капитал групп",
        "counterparty_type": "client",
        "inn": "2310123456",
        "kpp": "231001001",
        "phone": "+79001234567",
        "email": "info@kuban-kapital.ru",
        "address": "г. Краснодар, ул. Промышленная, 5",
        "contact_person": "Иванов Иван, менеджер",
        "notes": "Отсрочка 30 дней",
    }

    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ООО Кубань Капитал групп"
    assert data["counterparty_type"] == "client"
    assert data["inn"] == "2310123456"
    assert data["kpp"] == "231001001"
    assert data["phone"] == "+79001234567"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


async def test_create_counterparty_minimal(client: AsyncClient) -> None:
    """Минимальный набор полей."""
    payload = {
        "name": "Физлицо Иванов",
        "counterparty_type": "other",
    }

    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["inn"] is None
    assert data["kpp"] is None
    assert data["phone"] is None
    assert data["email"] is None


async def test_create_counterparty_normalizes_phone(client: AsyncClient) -> None:
    """Телефон 8... -> +7..."""
    payload = {
        "name": "ООО Тест",
        "counterparty_type": "client",
        "phone": "8 (978) 123-45-67",
    }

    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 201
    assert response.json()["phone"] == "+79781234567"


async def test_create_counterparty_duplicate_name_returns_409(
    client: AsyncClient, make_counterparty
) -> None:
    """Дубликат name → 409."""
    await make_counterparty(name="ООО Тест")

    payload = {"name": "ООО Тест", "counterparty_type": "client"}
    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "название" in detail.lower() or "существ" in detail.lower()


async def test_create_counterparty_invalid_type_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неизвестный counterparty_type -> 422."""
    payload = {"name": "Тест", "counterparty_type": "spaceship"}
    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 422


async def test_create_counterparty_invalid_inn_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неверный ИНН (5 цифр) -> 422."""
    payload = {
        "name": "Тест",
        "counterparty_type": "client",
        "inn": "12345",
    }

    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 422


async def test_create_counterparty_invalid_kpp_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неверный КПП → 422."""
    payload = {
        "name": "Тест",
        "counterparty_type": "client",
        "kpp": "12345",
    }
    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 422


async def test_create_counterparty_invalid_email_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Неверный email → 422."""
    payload = {
        "name": "Тест",
        "counterparty_type": "client",
        "email": "not-an-email",
    }
    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 422


async def test_create_counterparty_empty_name_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустое имя → 422."""
    payload = {"name": "", "counterparty_type": "client"}
    response = await client.post("/api/v1/counterparties/", json=payload)

    assert response.status_code == 422


async def test_list_counterparties_empty_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Пустая БД -> пустой список."""
    response = await client.get("/api/v1/counterparties/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_counterparties_returns_200(
    client: AsyncClient, make_counterparty
) -> None:
    """Возвращает всех созданных."""
    await make_counterparty(name="А")
    await make_counterparty(name="Б")
    await make_counterparty(name="В")

    response = await client.get("/api/v1/counterparties/")

    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_list_counterparties_filter_by_type(
    client: AsyncClient, make_counterparty
) -> None:
    """?counterparty_type=client фильтрует."""
    await make_counterparty(counterparty_type="client")
    await make_counterparty(counterparty_type="client")
    await make_counterparty(counterparty_type="rbu")

    response = await client.get("/api/v1/counterparties/?counterparty_type=client")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(c["counterparty_type"] == "client" for c in data)


async def test_list_counterparties_filter_by_status(
    client: AsyncClient, make_counterparty
) -> None:
    """?status=archived возвращает только архивные."""
    await make_counterparty(status="active")
    await make_counterparty(status="archived")

    response = await client.get("/api/v1/counterparties/?status=archived")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "archived"


async def test_list_counterparties_search_by_name(
    client: AsyncClient, make_counterparty
) -> None:
    """?search=Кубань находит по имени."""
    await make_counterparty(name="ООО Кубань Капитал групп")
    await make_counterparty(name="ООО Алгнит")

    response = await client.get("/api/v1/counterparties/?search=Кубань")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "ООО Кубань Капитал групп"


async def test_list_counterparties_search_by_inn(
    client: AsyncClient, make_counterparty
) -> None:
    """?search=2310123456 находит по ИНН."""
    await make_counterparty(name="ООО Тест1", inn="2310123456")
    await make_counterparty(name="ООО Тест2", inn="2310999999")

    response = await client.get("/api/v1/counterparties/?search=2310123456")

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_counterparties_pagination(
    client: AsyncClient, make_counterparty
) -> None:
    """?skip=1&limit=1 возвращает одну запись."""
    c1 = await make_counterparty(name="А")
    c2 = await make_counterparty(name="Б")
    await make_counterparty(name="В")

    response = await client.get("/api/v1/counterparties/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == c2.id
    assert c1.id != c2.id


async def test_get_counterparty_by_id_returns_200(
    client: AsyncClient, make_counterparty
) -> None:
    """GET /counterparties/{id} возвращает контрагента."""
    counterparty = await make_counterparty(name="ООО Тест")

    response = await client.get(f"/api/v1/counterparties/{counterparty.id}")

    assert response.status_code == 200
    assert response.json()["id"] == counterparty.id


async def test_get_counterparty_by_id_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий id → 404."""
    response = await client.get("/api/v1/counterparties/999999")

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


async def test_get_counterparty_by_id_too_large_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """id > int4 → 422."""
    too_large = 9_999_999_999_999_999_999
    response = await client.get(f"/api/v1/counterparties/{too_large}")

    assert response.status_code == 422


async def test_update_counterparty_returns_200(
    client: AsyncClient, make_counterparty
) -> None:
    """PATCH обновляет."""
    counterparty = await make_counterparty(name="ООО Старое")

    response = await client.patch(
        f"/api/v1/counterparties/{counterparty.id}",
        json={"name": "ООО Новое"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "ООО Новое"


async def test_update_counterparty_status_archived(
    client: AsyncClient, make_counterparty
) -> None:
    """Soft delete через status=archived."""
    counterparty = await make_counterparty(status="active")

    response = await client.patch(
        f"/api/v1/counterparties/{counterparty.id}",
        json={"status": "archived"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"


async def test_update_counterparty_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH несуществующего → 404."""
    response = await client.patch(
        "/api/v1/counterparties/999999",
        json={"name": "Тест"},
    )

    assert response.status_code == 404


async def test_update_counterparty_duplicate_name_returns_409(
    client: AsyncClient, make_counterparty
) -> None:
    """PATCH на чужое name → 409."""
    await make_counterparty(name="ООО Первое")
    c2 = await make_counterparty(name="ООО Второе")

    response = await client.patch(
        f"/api/v1/counterparties/{c2.id}",
        json={"name": "ООО Первое"},
    )

    assert response.status_code == 409
