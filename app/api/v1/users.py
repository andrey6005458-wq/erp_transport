from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user, get_user_by_id, list_users
from app.database.session import session_getter
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> User:
    """Создаёт пользователя.

    Хеширует пароль через CRUD. При дубликате email (unique constraint
    на users.email) возвращает 409 Conflict.
    """
    try:
        user = await create_user(db, user_in)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        ) from err
    return user


@router.get("/", response_model=list[UserRead])
async def list_users_endpoint(
    db: Annotated[AsyncSession, Depends(session_getter)],
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """Возвращает страницу пользователей с пагинацией.

    skip/limit — query-параметры (например, /users/?skip=0&limit=10).
    """
    return await list_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_endpoint(
    user_id: int,
    db: Annotated[AsyncSession, Depends(session_getter)],
) -> User:
    """Возвращает пользователя по id. 404 если не найден.

    user_id аннотирован int — FastAPI сам валидирует тип пути
    и вернёт 422 при нечисловом значении.
    """
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id={user_id} не найден",
        )
    return user
