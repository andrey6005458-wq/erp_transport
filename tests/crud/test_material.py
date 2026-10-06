import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.material import (
    create_material,
    get_material_by_id,
    get_material_by_name,
    list_materials,
    update_material,
)
from app.schemas.material import MaterialCreate, MaterialUpdate


async def test_create_material(db_session: AsyncSession) -> None:
    """Создание материала со всеми полями."""
    material = await create_material(
        db_session,
        MaterialCreate(
            name="Щебень 5-20",
            material_type="inert",
            unit="ton",
            is_bulk=True,
            density_kg_m3=1400,
            notes="Гранитный",
        ),
    )
    assert material.id is not None
    assert material.name == "Щебень 5-20"
    assert material.material_type == "inert"
    assert material.unit == "ton"
    assert material.is_bulk is True
    assert material.density_kg_m3 == 1400
    assert material.notes == "Гранитный"
    assert material.status == "active"


async def test_create_material_minimal(db_session: AsyncSession) -> None:
    """Минимальный набор полей, дефолты."""
    material = await create_material(
        db_session,
        MaterialCreate(
            name="Газоблок D500",
            material_type="building_material",
            unit="pallet",
        ),
    )
    assert material.is_bulk is False
    assert material.density_kg_m3 is None
    assert material.notes is None
    assert material.status == "active"


async def test_create_material_duplicate_name(db_session: AsyncSession) -> None:
    """Дубликат name -> IntegrityError."""
    await create_material(
        db_session,
        MaterialCreate(
            name="Щебень 5-20",
            material_type="inert",
            unit="ton",
        ),
    )

    with pytest.raises(IntegrityError):
        await create_material(
            db_session,
            MaterialCreate(
                name="Щебень 5-20",
                material_type="inert",
                unit="ton",
            ),
        )
    await db_session.rollback()


async def test_get_material_by_id(db_session: AsyncSession, make_material) -> None:
    """Получение материала по id."""
    created = await make_material()

    found = await get_material_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == created.name


async def test_get_material_by_id_not_found(db_session: AsyncSession) -> None:
    """Несуществующий id -> None."""
    found = await get_material_by_id(db_session, 999999)

    assert found is None


async def test_get_material_by_name(db_session: AsyncSession, make_material) -> None:
    """Получение материала по имени."""
    created = await make_material(name="Щебень 5-20")

    found = await get_material_by_name(db_session, "Щебень 5-20")

    assert found is not None
    assert found.id == created.id


async def test_get_material_by_name_not_found(db_session: AsyncSession) -> None:
    """Несуществующее имя -> None."""
    found = await get_material_by_name(db_session, "Несуществующий материал")

    assert found is None


async def test_list_materials_empty(db_session: AsyncSession) -> None:
    """Пустая БД -> пустой списко."""
    materials = await list_materials(db_session)

    assert materials == []


async def test_list_materials_returns_all(
    db_session: AsyncSession, make_material
) -> None:
    """Возвращает все созданные."""
    await make_material()
    await make_material()
    await make_material()

    materials = await list_materials(db_session)

    assert len(materials) == 3


async def test_list_materials_ordered_by_name(
    db_session: AsyncSession, make_material
) -> None:
    """Сортировка по name."""
    await make_material(name="Ящик")
    await make_material(name="Базальтовая вата")
    await make_material(name="Алебастр")

    materials = await list_materials(db_session)

    assert materials[0].name == "Алебастр"
    assert materials[1].name == "Базальтовая вата"
    assert materials[2].name == "Ящик"


async def test_list_materials_pagination(
    db_session: AsyncSession, make_material
) -> None:
    """skip/limit работают."""
    m1 = await make_material(name="А")
    m2 = await make_material(name="Б")
    await make_material(name="В")

    page = await list_materials(db_session, skip=1, limit=1)

    assert len(page) == 1
    assert page[0].id == m2.id
    assert m1.id != m2.id


async def test_list_materials_filter_by_status(
    db_session: AsyncSession, make_material
) -> None:
    """Фильтр по status."""
    await make_material(status="active")
    await make_material(status="active")
    await make_material(status="archived")

    active_only = await list_materials(db_session, status="active")
    archived_only = await list_materials(db_session, status="archived")

    assert len(active_only) == 2
    assert len(archived_only) == 1
    assert all(m.status == "active" for m in active_only)


async def test_list_materials_filter_by_type(
    db_session: AsyncSession, make_material
) -> None:
    """Фильтр по material_type."""
    await make_material(material_type="inert")
    await make_material(material_type="inert")
    await make_material(material_type="concrete")

    inert_only = await list_materials(db_session, material_type="inert")
    concrete_only = await list_materials(db_session, material_type="concrete")

    assert len(inert_only) == 2
    assert len(concrete_only) == 1
    assert all(m.material_type == "inert" for m in inert_only)


async def test_list_materials_search_by_name(
    db_session: AsyncSession, make_material
) -> None:
    """Поиск по name."""
    await make_material(name="Щебень 5-20")
    await make_material(name="Щебень 20-40")
    await make_material(name="Песок карьерный")

    found = await list_materials(db_session, search="Щебень")

    assert len(found) == 2


async def test_list_materials_search_case_insensitive(
    db_session: AsyncSession, make_material
) -> None:
    """Поиск нечувствителен к регистру."""
    await make_material(name="Щебень 5-20")

    found_lower = await list_materials(db_session, search="щебень")
    found_upper = await list_materials(db_session, search="ЩЕБЕНЬ")

    assert len(found_lower) == 1
    assert len(found_upper) == 1


async def test_list_materials_search_no_results(
    db_session: AsyncSession, make_material
) -> None:
    """Поиск без совпадений -> пустой список."""
    await make_material(name="Щебень 5-20")

    found = await list_materials(db_session, search="Несуществующий")

    assert found == []


async def test_update_material_name(db_session: AsyncSession, make_material) -> None:
    """Обновление name."""
    material = await make_material(name="Щебень")

    updated = await update_material(
        db_session, material, MaterialUpdate(name="Щебнь 5-20")
    )

    assert updated.name == "Щебнь 5-20"


async def test_update_material_status_archived(
    db_session: AsyncSession, make_material
) -> None:
    """Soft delete через status=archived."""
    material = await make_material(status="active")

    updated = await update_material(
        db_session, material, MaterialUpdate(status="archived")
    )

    assert updated.status == "archived"


async def test_update_material_density(db_session: AsyncSession, make_material) -> None:
    """Обновление density_kg_m3."""
    material = await make_material(density_kg_m3=None)

    updated = await update_material(
        db_session, material, MaterialUpdate(density_kg_m3=1400)
    )

    assert updated.density_kg_m3 == 1400


async def test_update_material_empty_patch(
    db_session: AsyncSession, make_material
) -> None:
    """PATCH {} не меняет ничего."""

    material = await make_material(name="Щебень", material_type="inert")
    original_name = material.name
    original_type = material.material_type

    updated = await update_material(db_session, material, MaterialUpdate())

    assert updated.name == original_name
    assert updated.material_type == original_type


async def test_update_material_notes_null(
    db_session: AsyncSession, make_material
) -> None:
    """Явная передача notes=None стирает поле."""
    material = await make_material(notes="важная заметка")
    assert material.notes == "важная заметка"

    updated = await update_material(db_session, material, MaterialUpdate(notes=None))

    assert updated.notes is None
