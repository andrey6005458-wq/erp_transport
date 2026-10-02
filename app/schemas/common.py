"""Общие Pydantic-типы, используемые в разных схемах и эндпоинтах."""

from typing import Annotated

from fastapi import Path

# Диапазон Postgres INTEGER (int4). Значения вне — БД не примет,
# поэтому валидируем на уровне FastAPI и возвращаем 422 вместо 500.
INT4_MAX = 2_147_483_647

RecordId = Annotated[int, Path(ge=1, le=INT4_MAX)]
