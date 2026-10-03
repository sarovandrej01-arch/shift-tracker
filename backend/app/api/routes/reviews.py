from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_review_service, require_moderator_or_admin
from app.core.enums import MessageReason
from app.models.telegram_message import TelegramMessage
from app.models.user import User
from app.schemas.review import (
    ReviewConfirmRequest,
    ReviewConfirmResponse,
    ReviewMessageRead,
    ReviewRejectRequest,
    ReviewRejectResponse,
)
from app.schemas.shift import ShiftRead
from app.services.review import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewMessageRead])
async def list_reviews(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    reason: MessageReason | None = Query(default=None),
    employee_id: int | None = Query(default=None),
    object_id: int | None = Query(default=None),
    date_from: date | None = Query(
        default=None,
        description="Inclusive UTC date lower bound for message created_at",
    ),
    date_to: date | None = Query(
        default=None,
        description="Inclusive UTC date upper bound for message created_at",
    ),
    _: User = Depends(require_moderator_or_admin),
    service: ReviewService = Depends(get_review_service),
) -> list[TelegramMessage]:
    return await service.list_reviews(
        offset=offset,
        limit=limit,
        reason=reason,
        employee_id=employee_id,
        object_id=object_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/{message_id}/confirm", response_model=ReviewConfirmResponse)
async def confirm_review(
    message_id: int,
    data: ReviewConfirmRequest,
    current_user: User = Depends(require_moderator_or_admin),
    service: ReviewService = Depends(get_review_service),
) -> ReviewConfirmResponse:
    result = await service.confirm(message_id, data, user_id=current_user.id)
    return ReviewConfirmResponse(
        message=ReviewMessageRead.model_validate(result.message),
        shift=ShiftRead.model_validate(result.shift),
    )


@router.post("/{message_id}/reject", response_model=ReviewRejectResponse)
async def reject_review(
    message_id: int,
    data: ReviewRejectRequest | None = None,
    current_user: User = Depends(require_moderator_or_admin),
    service: ReviewService = Depends(get_review_service),
) -> ReviewRejectResponse:
    message = await service.reject(
        message_id,
        data or ReviewRejectRequest(),
        user_id=current_user.id,
    )
    return ReviewRejectResponse(message=ReviewMessageRead.model_validate(message))
