from fastapi import APIRouter

from app.api.v1.absences import router as absences_router
from app.api.v1.driver_absences import router as driver_absences_router
from app.api.v1.drivers import router as drivers_router
from app.api.v1.materials import router as materials_router
from app.api.v1.users import router as user_router
from app.api.v1.vehicles import router as vehicles_router

api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(vehicles_router)
api_router.include_router(drivers_router)
api_router.include_router(driver_absences_router)
api_router.include_router(absences_router)
api_router.include_router(materials_router)
