from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_message_service, get_processing_log_service, require_moderator_or_admin
from app.core.enums import MessageReason, MessageStatus
from app.models.processing_log import ProcessingLog
from app.models.telegram_message import TelegramMessage
from app.models.user import User
from app.schemas.employee import EmployeeRead
from app.schemas.processing_log import ProcessingLogRead
from app.schemas.shift import ShiftRead
from app.schemas.telegram_message import MessageDetailRead, MessagePhotoUrlRead, TelegramMessageRead
from app.schemas.work_object import WorkObjectRead
from app.services.message import MessageDetail, MessageService
from app.services.processing_log import ProcessingLogService

router = APIRouter(prefix="/messages", tags=["messages"])


def _detail_response(detail: MessageDetail) -> MessageDetailRead:
    return MessageDetailRead(
        **TelegramMessageRead.model_validate(detail.message).model_dump(),
        employee=EmployeeRead.model_validate(detail.employee) if detail.employee is not None else None,
        work_object=WorkObjectRead.model_validate(detail.work_object) if detail.work_object is not None else None,
        shift=ShiftRead.model_validate(detail.shift) if detail.shift is not None else None,
    )


@router.get("", response_model=list[TelegramMessageRead])
async def list_messages(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    status: MessageStatus | None = Query(default=None),
    reason: MessageReason | None = Query(default=None),
    employee_id: int | None = Query(default=None),
    object_id: int | None = Query(default=None),
    telegram_chat_id: int | None = Query(default=None),
    telegram_user_id: int | None = Query(default=None),
    date_from: date | None = Query(
        default=None,
        description="Inclusive UTC date lower bound for message created_at",
    ),
    date_to: date | None = Query(
        default=None,
        description="Inclusive UTC date upper bound for message created_at",
    ),
    shift_date_from: date | None = Query(default=None),
    shift_date_to: date | None = Query(default=None),
    _: User = Depends(require_moderator_or_admin),
    service: MessageService = Depends(get_message_service),
) -> list[TelegramMessage]:
    return await service.list_messages(
        offset=offset,
        limit=limit,
        status=status,
        reason=reason,
        employee_id=employee_id,
        object_id=object_id,
        telegram_chat_id=telegram_chat_id,
        telegram_user_id=telegram_user_id,
        date_from=date_from,
        date_to=date_to,
        shift_date_from=shift_date_from,
        shift_date_to=shift_date_to,
    )


@router.get("/{message_id}/photo-url", response_model=MessagePhotoUrlRead)
async def get_message_photo_url(
    message_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: MessageService = Depends(get_message_service),
) -> MessagePhotoUrlRead:
    photo = await service.get_photo_url(message_id)
    return MessagePhotoUrlRead(
        message_id=photo.message_id,
        url=photo.url,
        expires_in=photo.expires_in,
    )


@router.get("/{message_id}/logs", response_model=list[ProcessingLogRead])
async def list_message_logs(
    message_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: ProcessingLogService = Depends(get_processing_log_service),
) -> list[ProcessingLog]:
    return await service.list_message_logs(message_id)


@router.get("/{message_id}", response_model=MessageDetailRead)
async def get_message(
    message_id: int,
    _: User = Depends(require_moderator_or_admin),
    service: MessageService = Depends(get_message_service),
) -> MessageDetailRead:
    return _detail_response(await service.get_message(message_id))
