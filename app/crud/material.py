from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialUpdate


async def create_material(
    db: AsyncSession,
    material_in: MaterialCreate,
) -> Material:
    """Создать материал."""
    material = Material(**material_in.model_dump())
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


async def get_material_by_id(
    db: AsyncSession,
    material_id: int,
) -> Material | None:
    """Возвращает материал по primary key."""
    return await db.get(Material, material_id)


async def get_material_by_name(
    db: AsyncSession,
    name: str,
) -> Material | None:
    """Возвращает материал по имени."""
    stmt = select(Material).where(Material.name == name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_materials(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    material_type: str | None = None,
    search: str | None = None,
) -> list[Material]:
    """Возвращает страницу материалов с фильтрами."""
    stmt = select(Material).order_by(Material.name).offset(skip).limit(limit)
    if status is not None:
        stmt = stmt.where(Material.status == status)
    if material_type is not None:
        stmt = stmt.where(Material.material_type == material_type)
    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(Material.name.ilike(pattern))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_material(
    db: AsyncSession,
    material: Material,
    material_in: MaterialUpdate,
) -> Material:
    """Частично обновить материал по PATCH семантике."""
    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    await db.commit()
    await db.refresh(material)
    return material
