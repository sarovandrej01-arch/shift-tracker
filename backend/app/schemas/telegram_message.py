from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import MessageReason, MessageStatus


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
    telegram_created_at: datetime
    edited_at: datetime | None
    employee_id: int | None
    object_id: int | None
    shift_date: date | None
    status: MessageStatus
    reason: MessageReason | None
    created_at: datetime
    updated_at: datetime
