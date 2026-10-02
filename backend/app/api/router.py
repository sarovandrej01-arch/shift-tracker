from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.employees import router as employees_router
from app.api.routes.test import router as test_router
from app.api.routes.users import router as users_router
from app.api.routes.work_objects import router as work_objects_router

api_router = APIRouter(prefix="/api")
api_router.include_router(test_router)
api_router.include_router(users_router, prefix="/v1")
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(employees_router, prefix="/v1")
api_router.include_router(work_objects_router, prefix="/v1")
