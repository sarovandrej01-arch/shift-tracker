from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_processing_log_service, require_moderator_or_admin
from app.models.processing_log import ProcessingLog
from app.models.user import User
from app.schemas.processing_log import ProcessingLogRead
from app.services.processing_log import ProcessingLogService

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[ProcessingLogRead])
async def list_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    message_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(
        default=None,
        description="Inclusive lower bound for created_at. Timezone-aware, for example 2026-10-03T00:00:00Z",
    ),
    date_to: datetime | None = Query(
        default=None,
        description="Inclusive upper bound for created_at. Timezone-aware, for example 2026-10-03T23:59:59Z",
    ),
    _: User = Depends(require_moderator_or_admin),
    service: ProcessingLogService = Depends(get_processing_log_service),
) -> list[ProcessingLog]:
    return await service.list_logs(
        offset=offset,
        limit=limit,
        message_id=message_id,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
    )
