from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_work_object_service,
    require_admin,
    require_moderator_or_admin,
)
from app.models.user import User
from app.models.work_object import WorkObject
from app.schemas.work_object import WorkObjectCreate, WorkObjectRead, WorkObjectUpdate
from app.services.work_object import WorkObjectService

router = APIRouter(prefix="/work-objects", tags=["work-objects"])


@router.post("", response_model=WorkObjectRead, status_code=status.HTTP_201_CREATED)
async def create_work_object(
    data: WorkObjectCreate,
    _: User = Depends(require_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> WorkObject:
    return await service.create_work_object(data)


@router.get("", response_model=list[WorkObjectRead])
async def list_work_objects(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    _: User = Depends(require_moderator_or_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> list[WorkObject]:
    return await service.list_work_objects(
        offset=offset,
        limit=limit,
        is_active=is_active,
        search=search,
    )


@router.get("/{object_id}", response_model=WorkObjectRead)
async def get_work_object(
    object_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> WorkObject:
    return await service.get_work_object(object_id)


@router.patch("/{object_id}", response_model=WorkObjectRead)
async def update_work_object(
    object_id: int,
    data: WorkObjectUpdate,
    _: User = Depends(require_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> WorkObject:
    return await service.update_work_object(object_id, data)


@router.post("/{object_id}/activate", response_model=WorkObjectRead)
async def activate_work_object(
    object_id: int,
    _: User = Depends(require_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> WorkObject:
    return await service.activate_work_object(object_id)


@router.post("/{object_id}/deactivate", response_model=WorkObjectRead)
async def deactivate_work_object(
    object_id: int,
    _: User = Depends(require_admin),
    service: WorkObjectService = Depends(get_work_object_service),
) -> WorkObject:
    return await service.deactivate_work_object(object_id)
