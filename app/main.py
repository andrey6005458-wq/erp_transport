from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.database.engine import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup: engine уже создан, соединения откроются при первом запросе
    yield
    # Shutdown: закрываем пул соединений
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def check_health():
    """Проверка живости приложения."""
    return {"status": "ok", "env": settings.app_env}
