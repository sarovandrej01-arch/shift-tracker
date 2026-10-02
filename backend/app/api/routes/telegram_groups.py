from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_telegram_group_service,
    require_admin,
    require_moderator_or_admin,
)
from app.models.telegram_group import TelegramGroup
from app.models.user import User
from app.schemas.telegram_group import TelegramGroupCreate, TelegramGroupRead, TelegramGroupUpdate
from app.services.telegram_group import TelegramGroupService

router = APIRouter(prefix="/telegram-groups", tags=["telegram-groups"])


@router.post("", response_model=TelegramGroupRead, status_code=status.HTTP_201_CREATED)
async def create_telegram_group(
    data: TelegramGroupCreate,
    _: User = Depends(require_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroup:
    return await service.create_telegram_group(data)


@router.get("", response_model=list[TelegramGroupRead])
async def list_telegram_groups(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    object_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(require_moderator_or_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> list[TelegramGroup]:
    return await service.list_telegram_groups(
        offset=offset,
        limit=limit,
        is_active=is_active,
        object_id=object_id,
        search=search,
    )


@router.get("/{group_id}", response_model=TelegramGroupRead)
async def get_telegram_group(
    group_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroup:
    return await service.get_telegram_group(group_id)


@router.patch("/{group_id}", response_model=TelegramGroupRead)
async def update_telegram_group(
    group_id: int,
    data: TelegramGroupUpdate,
    _: User = Depends(require_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroup:
    return await service.update_telegram_group(group_id, data)


@router.post("/{group_id}/activate", response_model=TelegramGroupRead)
async def activate_telegram_group(
    group_id: int,
    _: User = Depends(require_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroup:
    return await service.activate_telegram_group(group_id)


@router.post("/{group_id}/deactivate", response_model=TelegramGroupRead)
async def deactivate_telegram_group(
    group_id: int,
    _: User = Depends(require_admin),
    service: TelegramGroupService = Depends(get_telegram_group_service),
) -> TelegramGroup:
    return await service.deactivate_telegram_group(group_id)
