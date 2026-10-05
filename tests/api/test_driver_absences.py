from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_create_absence_returns_201(client: AsyncClient, make_driver) -> None:
    """POST создаёт отсутствие и возвращает 201."""
    driver = await make_driver()

    payload = {
        "absence_type": "vacation",
        "date_from": "2026-06-01",
        "date_to": "2026-06-14",
        "reason": "Ежегодный",
    }
    response = await client.post(
        f"/api/v1/drivers/{driver.id}/absences/",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["absence_type"] == "vacation"
    assert data["date_from"] == "2026-06-01"
    assert data["date_to"] == "2026-06-14"
    assert data["driver_id"] == driver.id


async def test_create_absence_has_driver_in_response(
    client: AsyncClient, make_driver
) -> None:
    """В ответе POST есть вложенный driver (регрессия на Вариант B)."""
    driver = await make_driver(last_name="Фомин", first_name="Дмитрий")

    payload = {
        "absence_type": "vacation",
        "date_from": "2026-06-01",
        "date_to": "2026-06-14",
    }
    response = await client.post(
        f"/api/v1/drivers/{driver.id}/absences/",
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert "driver" in data
    assert data["driver"]["id"] == driver.id
    assert data["driver"]["last_name"] == "Фомин"
    assert data["driver"]["first_name"] == "Дмитрий"


async def test_create_absence_driver_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий driver_id → 404."""
    payload = {
        "absence_type": "vacation",
        "date_from": "2026-06-01",
        "date_to": "2026-06-14",
    }
    response = await client.post(
        "/api/v1/drivers/999999/absences/",
        json=payload,
    )

    assert response.status_code == 404


async def test_create_absence_overlap_returns_409(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Пересечение с другим отсутствием -> 409."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )

    payload = {
        "absence_type": "other",
        "date_from": "2026-06-10",
        "date_to": "2026-06-20",
    }
    response = await client.post(
        f"/api/v1/drivers/{driver.id}/absences/",
        json=payload,
    )

    assert response.status_code == 409
    assert "пересека" in response.json()["detail"]


async def test_create_absence_invalid_dates_returns_422(
    client: AsyncClient, make_driver
) -> None:
    """date_to < date_from -> 422."""
    driver = await make_driver()

    payload = {
        "absence_type": "vacation",
        "date_from": "2026-06-14",
        "date_to": "2026-06-01",
    }
    response = await client.post(
        f"/api/v1/drivers/{driver.id}/absences/",
        json=payload,
    )

    assert response.status_code == 422


async def test_list_absences_empty_returns_200(
    client: AsyncClient, make_driver
) -> None:
    """Нет отсутствий -> пустой список."""
    driver = await make_driver()

    response = await client.get(f"/api/v1/drivers/{driver.id}/absences/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_absences_returns_with_driver(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Каждый элемент содержит driver (регрессия)."""
    driver = await make_driver(last_name="Фомин")
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 8, 1), date_to=date(2026, 8, 5)
    )

    response = await client.get(f"/api/v1/drivers/{driver.id}/absences/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert "driver" in item
        assert item["driver"]["last_name"] == "Фомин"


async def test_list_absences_filter_by_type(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?absence_type=vacation фильтрует."""
    driver = await make_driver()
    await make_absence(
        driver=driver,
        absence_type="sick_leave",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 5),
    )
    await make_absence(
        driver=driver,
        ansence_type="sick_leave",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 5),
    )

    response = await client.get(
        f"/api/v1/drivers/{driver.id}/absences/?absence_type=vacation"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["absence_type"] == "vacation"


async def test_list_abcences_driver_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Несуществующий driver_id -> 404."""
    response = await client.get("/api/v1/drivers/999999/absences/")

    assert response.status_code == 404


async def test_get_current_absence_return_200(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Возвращает текущее отсутствие с driver."""
    driver = await make_driver(last_name="Фомин")
    await make_absence(driver=driver, date_from=date.today(), date_to=None)

    response = await client.get(f"/api/v1/drivers/{driver.id}/absences/current")

    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == driver.id
    assert data["driver"]["last_name"] == "Фомин"


async def test_get_current_absence_not_found_returns_404(
    client: AsyncClient, make_driver
) -> None:
    """Нет текущего -> 404."""
    driver = await make_driver()

    response = await client.get(f"/api/v1/drivers/{driver.id}/absences/current")

    assert response.status_code == 404
    assert "нет текущего" in response.json()["detail"]


async def test_get_absence_by_id_returns_200(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """GET absence по id с driver."""
    driver = await make_driver(last_name="Фомин")
    absence = await make_absence(driver=driver)

    response = await client.get(f"/api/v1/drivers/{driver.id}/absences/{absence.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == absence.id
    assert data["driver"]["last_name"] == "Фомин"


async def test_get_absence_wrong_driver_returns_404(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Absence принадлежит другому водителю -> 404."""
    d1 = await make_driver()
    d2 = await make_driver()
    absence = await make_absence(driver=d1)

    response = await client.get(f"/api/v1/drivers/{d2.id}/absences/{absence.id}")

    assert response.status_code == 404


async def test_update_absence_returns_200(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """PATCH обновляет и возвращает driver."""
    driver = await make_driver(last_name="Фомин")
    absence = await make_absence(driver=driver, reason="Старая")

    response = await client.patch(
        f"/api/v1/drivers/{driver.id}/absences/{absence.id}",
        json={"reason": "Новая"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reason"] == "Новая"
    assert data["driver"]["last_name"] == "Фомин"


async def test_update_absence_overlap_returns_409(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """PATCH с пересечением → 409."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )
    a2 = await make_absence(
        driver=driver, date_from=date(2026, 7, 1), date_to=date(2026, 7, 5)
    )

    response = await client.patch(
        f"/api/v1/drivers/{driver.id}/absences/{a2.id}",
        json={"date_from": "2026-06-10"},
    )

    assert response.status_code == 409


async def test_update_absence_not_found_returns_404(
    client: AsyncClient, make_driver
) -> None:
    """PATCH несуществующего → 404."""
    driver = await make_driver()

    response = await client.patch(
        f"/api/v1/drivers/{driver.id}/absences/999999",
        json={"reason": "X"},
    )

    assert response.status_code == 404


async def test_delete_absence_returns_204(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """DELETE возвращает 204, absence исчезает."""
    driver = await make_driver()
    absence = await make_absence(driver=driver)

    response = await client.delete(f"/api/v1/drivers/{driver.id}/absences/{absence.id}")

    assert response.status_code == 204

    check = await client.get(f"/api/v1/drivers/{driver.id}/absences/{absence.id}")
    assert check.status_code == 404


async def test_deleteabsence_not_found_returns_404(
    client: AsyncClient, make_driver
) -> None:
    """DELETE несуществующего -> 404."""
    driver = await make_driver()

    response = await client.delete(f"/api/v1/drivers/{driver.id}/absences/999999")

    assert response.status_code == 404
