from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_REQUIRED_UPDATE_FIELDS = (
    "name",
    "shift_start_time",
    "checkin_before_minutes",
    "checkin_after_minutes",
    "timezone",
    "is_active",
)


def validate_timezone(value: str) -> str:
    normalized = value.strip()
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Invalid timezone") from exc
    return normalized


def _required_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be empty")
    return normalized


class WorkObjectBase(BaseModel):
    name: str
    shift_start_time: time
    checkin_before_minutes: int = Field(ge=0)
    checkin_after_minutes: int = Field(ge=0)
    timezone: str = "Europe/Moscow"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return _required_name(value)

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_timezone(value)


class WorkObjectCreate(WorkObjectBase):
    is_active: bool = True


class WorkObjectUpdate(BaseModel):
    name: str | None = None
    shift_start_time: time | None = None
    checkin_before_minutes: int | None = Field(default=None, ge=0)
    checkin_after_minutes: int | None = Field(default=None, ge=0)
    timezone: str | None = None
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

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_timezone(value)


class WorkObjectRead(WorkObjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
