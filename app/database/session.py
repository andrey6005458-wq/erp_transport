from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import async_session_maker


async def session_getter() -> AsyncGenerator[AsyncSession]:
    """Зависимость FastAPI: даёт сессию Базе Данных на время запроса."""

    async with async_session_maker() as session:
        yield session
