from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import MessageReason, MessageStatus
from app.schemas.employee import EmployeeRead
from app.schemas.shift import ShiftRead
from app.schemas.work_object import WorkObjectRead


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class TelegramMessageCreate(BaseModel):
    telegram_chat_id: int
    telegram_message_id: int
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    text: str | None = None
    caption: str | None = None
    photo_file_id: str | None = None
    photo_storage_key: str | None = None
    telegram_created_at: datetime

    @field_validator("telegram_username", "text", "caption", "photo_file_id", "photo_storage_key")
    @classmethod
    def blank_optional_to_none(cls, value: str | None) -> str | None:
        return _blank_to_none(value)

    @field_validator("telegram_created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("telegram_created_at must be timezone-aware")
        return value


class TelegramMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_message_id: int
    telegram_chat_id: int
    telegram_user_id: int | None
    telegram_username: str | None
    text: str | None
    caption: str | None
    photo_file_id: str | None
    photo_storage_key: str | None
    telegram_created_at: datetime
    edited_at: datetime | None
    employee_id: int | None
    object_id: int | None
    shift_date: date | None
    status: MessageStatus
    reason: MessageReason | None
    created_at: datetime
    updated_at: datetime


class MessageDetailRead(TelegramMessageRead):
    employee: EmployeeRead | None = None
    work_object: WorkObjectRead | None = None
    shift: ShiftRead | None = None


class MessagePhotoUrlRead(BaseModel):
    message_id: int
    url: str
    expires_in: int
