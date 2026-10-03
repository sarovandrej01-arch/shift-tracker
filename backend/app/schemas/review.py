from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import MessageReason, MessageStatus
from app.schemas.shift import ShiftRead


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class ReviewMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_message_id: int
    telegram_chat_id: int
    telegram_user_id: int | None
    telegram_username: str | None
    text: str | None
    caption: str | None
    photo_storage_key: str | None
    telegram_created_at: datetime
    employee_id: int | None
    object_id: int | None
    shift_date: date | None
    status: MessageStatus
    reason: MessageReason | None
    created_at: datetime
    updated_at: datetime


class ReviewConfirmRequest(BaseModel):
    employee_id: int | None = None
    object_id: int | None = None
    shift_date: date | None = None


class ReviewRejectRequest(BaseModel):
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def blank_comment_to_none(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class ReviewConfirmResponse(BaseModel):
    message: ReviewMessageRead
    shift: ShiftRead


class ReviewRejectResponse(BaseModel):
    message: ReviewMessageRead
