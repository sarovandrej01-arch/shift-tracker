from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _strip_required(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be empty")
    return normalized


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class EmployeeBase(BaseModel):
    full_name: str
    personnel_number: str
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    callsign: str | None = None

    @field_validator("full_name", "personnel_number")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("telegram_username", "callsign")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class EmployeeCreate(EmployeeBase):
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    personnel_number: str | None = None
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    callsign: str | None = None
    is_active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            for field in ("full_name", "personnel_number", "is_active"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} cannot be null")
        return data

    @field_validator("full_name", "personnel_number")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)

    @field_validator("telegram_username", "callsign")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
