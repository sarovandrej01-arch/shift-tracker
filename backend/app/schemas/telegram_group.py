from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

_REQUIRED_UPDATE_FIELDS = (
    "telegram_chat_id",
    "name",
    "object_id",
    "is_active",
)


def _required_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be empty")
    return normalized


class TelegramGroupBase(BaseModel):
    telegram_chat_id: int
    name: str
    object_id: int

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return _required_name(value)


class TelegramGroupCreate(TelegramGroupBase):
    is_active: bool = True


class TelegramGroupUpdate(BaseModel):
    telegram_chat_id: int | None = None
    name: str | None = None
    object_id: int | None = None
    is_active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            for field in _REQUIRED_UPDATE_FIELDS:
                if field in data and data[field] is None:
                    raise ValueError(f"{field} cannot be null")
        return data

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _required_name(value)


class TelegramGroupRead(TelegramGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
