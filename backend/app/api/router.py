from fastapi import APIRouter

from app.api.routes.test import router as test_router

api_router = APIRouter(prefix="/api")
api_router.include_router(test_router)
