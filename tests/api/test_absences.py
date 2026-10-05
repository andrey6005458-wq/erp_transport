from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_list_absences_no_params_returns_400(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Без параметров -> 400 с подсказкой."""
    response = await client.get("/api/v1/absences/")

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "date" in detail.lower() or "period" in detail.lower()


async def test_list_absences_on_date_returns_matching(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?date= возвращает тех, кто отсутствовал в этот день."""
    driver = await make_driver(last_name="Фомин")
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )

    response = await client.get("/api/v1/absences/?date=2026-06-07")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["driver_id"] == driver.id
    assert data[0]["driver"]["last_name"] == "Фомин"


async def test_list_absences_on_date_no_match_returns_empty(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?date= вне периода → пустой список."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )

    response = await client.get("/api/v1/absences/?date=2026-07-01")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_absences_on_date_open_ended(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """Открытое отсутствие попадает в любую будущую дату."""
    driver = await make_driver()
    await make_absence(driver=driver, date_from=date(2026, 10, 1), date_to=None)

    response = await client.get("/api/v1/absences/?date=2027-01-01")

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_absences_in_period_returns_overlapping(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?period_from=&period_to= возвращает пересекающиеся."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 6, 20), date_to=date(2026, 6, 25)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 12, 1), date_to=date(2026, 12, 5)
    )

    response = await client.get(
        "/api/v1/absences/?period_from=2026-06-01&period_to=2026-06-30"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_absences_in_repiod_only_from_returns_400(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Только period_from без period_to -> 400."""
    response = await client.get("/api/v1/absences/?period_from=2026-06-01")

    assert response.status_code == 400


async def test_list_absences_in_period_only_to_returns_400(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Только period_to без period_from -> 400."""
    response = await client.get("/api/v1/absences/?period_to=2026-06-30")

    assert response.status_code == 400


async def test_list_absences_filter_by_driver_id(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?date= + driver_id фильтрует по водителю."""
    d1 = await make_driver()
    d2 = await make_driver()
    await make_absence(driver=d1, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14))
    await make_absence(driver=d2, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14))

    response = await client.get(f"/api/v1/absences/?date=2026-06-07&driver_id={d1.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["driver_id"] == d1.id


async def test_list_absences_filter_by_type(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?date= + absence_type фильтрует по типу."""
    driver = await make_driver()
    await make_absence(
        driver=driver,
        absence_type="vacation",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 14),
    )
    await make_absence(
        driver=driver,
        absence_type="sick_leave",
        date_from=date(2026, 6, 20),
        date_to=date(2026, 6, 25),
    )

    response = await client.get(
        "/api/v1/absences/?date=2026-06-07&absence_type=vacation"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["absence_type"] == "vacation"


async def test_list_absences_in_period_filter_by_type(
    client: AsyncClient, make_driver, make_absence
) -> None:
    """?period + absence_type."""
    driver = await make_driver()
    await make_absence(
        driver=driver,
        absence_type="vacation",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 14),
    )
    await make_absence(
        driver=driver,
        absence_type="sick_leave",
        date_from=date(2026, 6, 20),
        date_to=date(2026, 6, 25),
    )

    response = await client.get(
        "/api/v1/absences/?period_from=2026-06-01&period_to=2026-06-30"
        "&absence_type=sick_leave"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["absence_type"] == "sick_leave"
