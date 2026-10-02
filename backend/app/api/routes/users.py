from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_user_service
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.create_user(data)


@router.get("", response_model=list[UserRead])
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    service: UserService = Depends(get_user_service),
) -> list[User]:
    return await service.list_users(
        offset=offset,
        limit=limit,
        is_active=is_active,
        role=role,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.update_user(user_id, data)


@router.post("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.activate_user(user_id)


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.deactivate_user(user_id)
