from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Создаёт нового пользователя."""
    hashed_password = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        phone=user_in.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Возвращает пользователя по primary key."""
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Возвращает пользователя по email."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Возвращает страницу пользователей, отсортированных по id."""
    stmt = select(User).offset(skip).limit(limit).order_by(User.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_user(
    db: AsyncSession,
    user: User,
    user_in: UserUpdate,
) -> User:
    """Частично обновляет пользователя по PATCH-семантике."""
    update_data = user_in.model_dump(exclude_unset=True)

    if update_data.get("password") is not None:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user
