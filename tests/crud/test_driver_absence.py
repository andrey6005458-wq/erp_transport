from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.driver_absence import (
    create_absence,
    delete_absence,
    get_absence_by_id,
    get_current_absence_by_driver,
    list_absences_by_driver,
    list_absences_in_period,
    list_absences_on_date,
    list_current_absences,
    update_absence,
)
from app.schemas.driver_absence import DriverAbsenceCreate, DriverAbsenceUpdate


async def test_create_absence(db_session: AsyncSession, make_driver) -> None:
    """Создание отсутствия со всеми полями."""
    driver = await make_driver()

    absence = await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
            reason="Ежегодный оплачиваемый отпуск",
        ),
    )

    assert absence.id is not None
    assert absence.driver_id == driver.id
    assert absence.absence_type == "vacation"
    assert absence.date_from == date(2026, 6, 1)
    assert absence.date_to == date(2026, 6, 14)
    assert absence.reason == "Ежегодный оплачиваемый отпуск"


async def test_create_absence_open_ended(db_session: AsyncSession, make_driver) -> None:
    """date_to=None — водитель еще не вернулся."""
    driver = await make_driver()

    absence = await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="sick_leave",
            date_from=date(2026, 10, 1),
        ),
    )

    assert absence.date_to is None
    assert absence.absence_type == "sick_leave"


async def test_create_absence_has_driver_loaded(
    db_session: AsyncSession, make_driver
) -> None:
    """После create_absence связь driver подгружена (selectinload)."""
    driver = await make_driver(last_name="Фомин", first_name="Дмитрий")

    absence = await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
        ),
    )

    assert absence.driver is not None
    assert absence.driver.id == driver.id
    assert absence.driver.last_name == "Фомин"
    assert absence.driver.first_name == "Дмитрий"


async def test_create_absence_overlap_with_open_ended(
    db_session: AsyncSession, make_driver
) -> None:
    """Пересечение с открытым (date_to=None) → ValueError."""
    driver = await make_driver()
    await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="sick_leave",
            date_from=date(2026, 10, 1),
        ),
    )

    with pytest.raises(ValueError, match="пересекающееся"):
        await create_absence(
            db_session,
            driver_id=driver.id,
            absence_in=DriverAbsenceCreate(
                absence_type="vacation",
                date_from=date(2026, 12, 1),
                date_to=date(2026, 12, 5),
            ),
        )


async def test_create_absence_overlap_with_closed(
    db_session: AsyncSession, make_driver
) -> None:
    """Пересечение с закрытым периодом -> ValueError."""
    driver = await make_driver()
    await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
        ),
    )

    with pytest.raises(ValueError, match="пересекающееся"):
        await create_absence(
            db_session,
            driver_id=driver.id,
            absence_in=DriverAbsenceCreate(
                absence_type="other",
                date_from=date(2026, 6, 10),
                date_to=date(2026, 6, 20),
            ),
        )


async def test_create_absence_adjacent_dates_ok(
    db_session: AsyncSession, make_driver
) -> None:
    """Соседние периоды (date_to=X, date_from=X+1) — не пересекаются."""
    driver = await make_driver()
    await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
        ),
    )

    absence = await create_absence(
        db_session,
        driver_id=driver.id,
        absence_in=DriverAbsenceCreate(
            absence_type="other",
            date_from=date(2026, 6, 15),
            date_to=date(2026, 6, 20),
        ),
    )

    assert absence.id is not None


async def test_create_absence_other_driver_ok(
    db_session: AsyncSession, make_driver
) -> None:
    """Отсутствия разных водителей не пересакаются."""
    d1 = await make_driver()
    d2 = await make_driver()

    await create_absence(
        db_session,
        driver_id=d1.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
        ),
    )

    absence = await create_absence(
        db_session,
        driver_id=d2.id,
        absence_in=DriverAbsenceCreate(
            absence_type="vacation",
            date_from=date(2026, 6, 1),
            date_to=date(2026, 6, 14),
        ),
    )

    assert absence.id is not None


async def test_get_absence_by_id(db_session: AsyncSession, make_absence) -> None:
    """Получение отсутствия по id."""
    created = await make_absence()

    found = await get_absence_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id


async def test_get_absence_by_id_has_driver_loaded(
    db_session: AsyncSession, make_absence
) -> None:
    """driver подгружен через selectinload (регрессия на Вариант В)."""
    created = await make_absence()

    found = await get_absence_by_id(db_session, created.id)

    assert found is not None
    assert found.driver is not None
    assert found.driver.id == found.driver_id


async def test_get_absence_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id -> None."""
    found = await get_absence_by_id(db_session, 999999)

    assert found is None


async def test_list_absences_by_driver_empty(
    db_session: AsyncSession, make_driver
) -> None:
    """Нет отсутствий -> пустой список."""
    driver = await make_driver()

    absences = await list_absences_by_driver(db_session, driver.id)

    assert absences == []


async def test_list_absences_by_driver_returns_all(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Возвращает все отсутствия водителя."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 1, 1), date_to=date(2026, 1, 5)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 3, 1), date_to=date(2026, 3, 5)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 5, 1), date_to=date(2026, 5, 5)
    )

    absences = await list_absences_by_driver(db_session, driver.id)

    assert len(absences)


async def test_list_absences_by_driver_filter_by_type(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Фильтр по absence_type."""
    driver = await make_driver()
    await make_absence(
        driver=driver,
        absence_type="vacation",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 5),
    )
    await make_absence(
        driver=driver,
        absence_type="sick_leave",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 5),
    )
    await make_absence(
        driver=driver,
        absence_type="vacation",
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 5),
    )

    vacations = await list_absences_by_driver(
        db_session, driver.id, absence_type="vacation"
    )
    sick = await list_absences_by_driver(
        db_session, driver.id, absence_type="sick_leave"
    )

    assert len(vacations) == 2
    assert len(sick) == 1
    assert all(a.absence_type == "vacation" for a in vacations)


async def test_list_absences_by_driver_ordered_desc(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Сортировка по date_from DESC."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 1, 1), date_to=date(2026, 1, 5)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 5, 1), date_to=date(2026, 5, 5)
    )
    await make_absence(
        driver=driver, date_from=date(2026, 3, 1), date_to=date(2026, 3, 5)
    )

    absences = await list_absences_by_driver(db_session, driver.id)

    assert absences[0].date_from == date(2026, 5, 1)
    assert absences[1].date_from == date(2026, 3, 1)
    assert absences[2].date_from == date(2026, 1, 1)


async def test_list_absences_by_driver_has_driver_loaded(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Каждый элемент содержит driver (регрессия на Вариант В)."""
    driver = await make_driver(last_name="Фомин")
    await make_absence(driver=driver)
    await make_absence(
        driver=driver, date_from=date(2026, 5, 1), date_to=date(2026, 5, 5)
    )

    absences = await list_absences_by_driver(db_session, driver.id)

    for a in absences:
        assert a.driver is not None
        assert a.driver.last_name == "Фомин"


async def test_update_absence_reason(db_session: AsyncSession, make_absence) -> None:
    """Обновление reason."""
    absence = await make_absence(reason="Старая причина")

    updated = await update_absence(
        db_session, absence, DriverAbsenceUpdate(reason="Новая причина")
    )

    assert updated.reason == "Новая причина"


async def test_update_absence_close_open_ended(
    db_session: AsyncSession, make_absence
) -> None:
    """Закрыть открытое отсутствие (date_to=None -> date)."""
    absence = await make_absence(
        absence_type="sick_leave",
        date_from=date(2026, 10, 1),
        date_to=None,
    )
    assert absence.date_to is None

    updated = await update_absence(
        db_session, absence, DriverAbsenceUpdate(date_to=date(2026, 10, 15))
    )

    assert updated.date_to == date(2026, 10, 15)


async def test_update_absence_overlap_raises(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Обновление с пересечением -> ValueError."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )
    a2 = await make_absence(
        driver=driver, date_from=date(2026, 7, 1), date_to=date(2026, 7, 5)
    )

    with pytest.raises(ValueError, match="пересечение"):
        await update_absence(
            db_session,
            a2,
            DriverAbsenceUpdate(date_from=date(2026, 6, 10)),
        )


async def test_update_absence_excludes_self(
    db_session: AsyncSession, make_absence
) -> None:
    """Обновление одного absence не ловит себя самого (exclude_absence_id)."""
    absence = await make_absence(date_from=date(2026, 6, 1), date_to=date(2026, 6, 14))

    updated = await update_absence(
        db_session, absence, DriverAbsenceUpdate(date_to=date(2026, 6, 20))
    )

    assert updated.date_to == date(2026, 6, 20)


async def test_update_absence_invalid_dates(
    db_session: AsyncSession, make_absence
) -> None:
    """date_to < date_from -> ValueError."""
    absence = await make_absence(date_from=date(2026, 6, 1), date_to=date(2026, 6, 14))

    with pytest.raises(ValueError, match="date_to"):
        await update_absence(
            db_session, absence, DriverAbsenceUpdate(date_to=date(2026, 5, 1))
        )


async def test_delete_absence(db_session: AsyncSession, make_absence) -> None:
    """После удаления absence не находится."""
    absence = await make_absence()
    absence_id = absence.id

    await delete_absence(db_session, absence)

    found = await get_absence_by_id(db_session, absence_id)
    assert found is None


async def test_list_current_absences_returns_active(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Только те, что покрывают сегодня."""
    today = date.today()
    d_active = await make_driver()
    d_future = await make_driver()

    # Активное сегодня
    await make_absence(driver=d_active, date_from=today, date_to=None)
    # Будущее — не должно попасть
    await make_absence(
        driver=d_future,
        date_from=date(2099, 1, 1),
        date_to=date(2099, 1, 5),
    )

    current = await list_current_absences(db_session)

    assert len(current) == 1
    assert current[0].date_from == today
    assert current[0].driver_id == d_active.id


async def test_get_current_absence_by_driver_found(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Находит текущее отсутствие водителя."""
    today = date.today()
    driver = await make_driver()
    await make_absence(driver=driver, date_from=today, date_to=None)

    found = await get_current_absence_by_driver(db_session, driver.id)

    assert found is not None
    assert found.driver_id == driver.id


async def test_get_current_absence_by_driver_not_found(
    db_session: AsyncSession, make_driver
) -> None:
    """Нет текущего отсутствия -> None."""
    driver = await make_driver()

    found = await get_current_absence_by_driver(db_session, driver.id)

    assert found is None


async def test_list_absences_on_date_within(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Отсутствия, покрывающие указанную дату."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )

    absences = await list_absences_on_date(db_session, date(2026, 6, 7))

    assert len(absences) == 1


async def test_list_absences_on_date_outside(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Отвутствия вне даты не попадают."""
    driver = await make_driver()
    await make_absence(
        driver=driver, date_from=date(2026, 6, 1), date_to=date(2026, 6, 14)
    )

    absences = await list_absences_on_date(db_session, date(2026, 7, 1))

    assert absences == []


async def test_list_absences_in_period_overlapping(
    db_session: AsyncSession, make_driver, make_absence
) -> None:
    """Отсутствия, пересекающиеся с периодом."""
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

    absences = await list_absences_in_period(
        db_session, period_from=date(2026, 6, 1), period_to=date(2026, 6, 30)
    )

    assert len(absences) == 2
