import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.counterparty import (
    create_counterparty,
    get_counterparty_by_id,
    get_counterparty_by_name,
    list_counterparties,
    update_counterparty,
)
from app.schemas.counterparty import CounterpartyCreate, CounterpartyUpdate


async def test_create_counterparty(db_session: AsyncSession) -> None:
    """Создание контрагента со всеми полями."""
    counterparty = await create_counterparty(
        db_session,
        CounterpartyCreate(
            name="ООО Кубань Капитал групп",
            counterparty_type="client",
            inn="2310123456",
            kpp="231001001",
            phone="+79001234567",
            email="info@kuban-kapital.ru",
            address="г. Краснодар, ул. Промышленная, 5",
            contact_person="Иванов Иван, менеджер",
            notes="Отсрочка 30 дней",
        ),
    )
    assert counterparty.id is not None
    assert counterparty.name == "ООО Кубань Капитал групп"
    assert counterparty.counterparty_type == "client"
    assert counterparty.inn == "2310123456"
    assert counterparty.kpp == "231001001"
    assert counterparty.phone == "+79001234567"
    assert counterparty.email == "info@kuban-kapital.ru"
    assert counterparty.status == "active"


async def test_create_counterparty_minimal(db_session: AsyncSession) -> None:
    """Минимальный набор полей."""
    counterparty = await create_counterparty(
        db_session,
        CounterpartyCreate(
            name="Физлицо Иванов",
            counterparty_type="other",
        ),
    )
    assert counterparty.id is not None
    assert counterparty.inn is None
    assert counterparty.kpp is None
    assert counterparty.phone is None
    assert counterparty.email is None
    assert counterparty.status == "active"


async def test_create_counterparty_normalizes_phone(
    db_session: AsyncSession,
) -> None:
    """Телефон 8... → +7..."""
    counterparty = await create_counterparty(
        db_session,
        CounterpartyCreate(
            name="ООО Тест",
            counterparty_type="client",
            phone="89001234567",
        ),
    )
    assert counterparty.phone == "+79001234567"


async def test_create_counterparty_duplicate_name(
    db_session: AsyncSession,
) -> None:
    """Дубликат name → IntegrityError."""
    await create_counterparty(
        db_session,
        CounterpartyCreate(name="ООО Тест", counterparty_type="client"),
    )

    with pytest.raises(IntegrityError):
        await create_counterparty(
            db_session,
            CounterpartyCreate(name="ООО Тест", counterparty_type="supplier"),
        )
    await db_session.rollback()


async def test_get_counterparty_by_id(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Получение по id."""
    created = await make_counterparty()

    found = await get_counterparty_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id


async def test_get_counterparty_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id → None."""
    found = await get_counterparty_by_id(db_session, 999999)

    assert found is None


async def test_get_counterparty_by_name(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Получение по имени."""
    created = await make_counterparty(name="ООО Тест")

    found = await get_counterparty_by_name(db_session, "ООО Тест")

    assert found is not None
    assert found.id == created.id


async def test_get_counterparty_by_name_not_found(db_session: AsyncSession) -> None:
    """Несуществующее имя → None."""
    found = await get_counterparty_by_name(db_session, "Несуществующий")

    assert found is None


async def test_list_counterparties_empty(db_session: AsyncSession) -> None:
    """Пустая БД -> пустой список."""
    result = await list_counterparties(db_session)

    assert result == []


async def test_list_counterparties_returns_all(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Возвращает всех созданных."""
    await make_counterparty()
    await make_counterparty()
    await make_counterparty()

    result = await list_counterparties(db_session)

    assert len(result) == 3


async def test_list_counterparties_ordered_by_name(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Сортировка по name."""
    await make_counterparty(name="ООО Яблоко")
    await make_counterparty(name="ООО Апельсин")
    await make_counterparty(name="ООО Банан")

    result = await list_counterparties(db_session)

    assert result[0].name == "ООО Апельсин"
    assert result[1].name == "ООО Банан"
    assert result[2].name == "ООО Яблоко"


async def test_list_counterparties_pagination(
    db_session: AsyncSession, make_counterparty
) -> None:
    """skip/limit работают."""
    c1 = await make_counterparty(name="А")
    c2 = await make_counterparty(name="Б")
    await make_counterparty(neme="В")

    page = await list_counterparties(db_session, skip=1, limit=1)

    assert len(page) == 1
    assert page[0].id == c2.id
    assert c1.id != c2.id


async def test_list_counterparties_filter_by_status(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Фильтр по status."""
    await make_counterparty(status="active")
    await make_counterparty(status="active")
    await make_counterparty(status="archived")

    active_only = await list_counterparties(db_session, status="active")
    archived_only = await list_counterparties(db_session, status="archived")

    assert len(active_only) == 2
    assert len(archived_only) == 1
    assert all(c.status == "active" for c in active_only)


async def test_list_counterparties_filter_by_type(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Фильтр по counterparty_type."""
    await make_counterparty(counterparty_type="client")
    await make_counterparty(counterparty_type="client")
    await make_counterparty(counterparty_type="rbu")

    clients = await list_counterparties(db_session, counterparty_type="client")
    rbus = await list_counterparties(db_session, counterparty_type="rbu")

    assert len(clients) == 2
    assert len(rbus) == 1


async def test_list_counterparties_search_by_name(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Поиск по name."""
    await make_counterparty(name="ООО Кубань Капиталл групп")
    await make_counterparty(name="ООО Алгнит")
    await make_counterparty(name="ООО Кубаньстрой")

    found = await list_counterparties(db_session, search="Кубань")

    assert len(found) == 2


async def test_list_counterparties_search_by_inn(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Поиск по ИНН."""
    await make_counterparty(name="ООО Тест1", inn="2310123456")
    await make_counterparty(name="ООО Тест2", inn="2310999999")

    found = await list_counterparties(db_session, search="2310999999")

    assert len(found) == 1
    assert found[0].inn == "2310999999"


async def test_list_counterparties_search_no_results(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Поиск без совпадений -> пусто."""
    await make_counterparty(name="ООО тест")

    found = await list_counterparties(db_session, search="Несуществующий")

    assert found == []


async def test_update_counterparty_name(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Обновление name."""
    counterparty = await make_counterparty(name="ООО Старое")

    updated = await update_counterparty(
        db_session,
        counterparty,
        CounterpartyUpdate(name="ООО Новое"),
    )

    assert updated.name == "ООО Новое"


async def test_update_counterparty_status_archived(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Soft delete через status=archived."""
    counterparty = await make_counterparty(status="active")

    updated = await update_counterparty(
        db_session,
        counterparty,
        CounterpartyUpdate(status="archived"),
    )

    assert updated.status == "archived"


async def test_update_counterparty_phone_normalized(
    db_session: AsyncSession, make_counterparty
) -> None:
    """phone нормализуется при update."""
    counterparty = await make_counterparty(phone="+79781234567")

    updated = await update_counterparty(
        db_session,
        counterparty,
        CounterpartyUpdate(phone="8 (978) 123-45-67"),
    )

    assert updated.phone == "+79781234567"


async def test_update_counterparty_empty_patch(
    db_session: AsyncSession, make_counterparty
) -> None:
    """PATCH {} не меняет ничего."""
    counterparty = await make_counterparty(name="ООО Тест", counterparty_type="client")
    original_name = counterparty.name
    original_type = counterparty.counterparty_type

    updated = await update_counterparty(db_session, counterparty, CounterpartyUpdate())

    assert updated.name == original_name
    assert updated.counterparty_type == original_type


async def test_update_counterparty_notes_null(
    db_session: AsyncSession, make_counterparty
) -> None:
    """Явная передача notes=None стирает поле."""
    counterparty = await make_counterparty(notes="важная заметка")
    assert counterparty.notes == "важная заметка"

    updated = await update_counterparty(
        db_session, counterparty, CounterpartyUpdate(notes=None)
    )

    assert updated.notes is None
