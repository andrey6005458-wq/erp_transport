import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.database.engine import async_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup: engine создан, соединения откроются при первом запросе
    yield
    # Shutdown: закрываем пул соединений
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health():
    """Liveness: приложение живо."""
    return {
        "status": "ok",
        "version": app.version,
        "env": settings.app_env,
    }


@app.get("/ready", tags=["Health"])
async def ready():
    """Readiness: приложение готово принимать трафик."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
