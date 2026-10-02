from fastapi import APIRouter

from app.api.v1.users import router as user_router
from app.api.v1.vehicles import router as vehicles_router

api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(vehicles_router)
