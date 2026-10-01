from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelegramGroupBase(BaseModel):
    telegram_chat_id: int
    name: str
    object_id: int


class TelegramGroupCreate(TelegramGroupBase):
    is_active: bool = True


class TelegramGroupUpdate(BaseModel):
    telegram_chat_id: int | None = None
    name: str | None = None
    object_id: int | None = None
    is_active: bool | None = None


class TelegramGroupRead(TelegramGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
