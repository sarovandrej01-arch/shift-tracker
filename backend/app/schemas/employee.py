from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmployeeBase(BaseModel):
    full_name: str
    personnel_number: str
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    callsign: str | None = None


class EmployeeCreate(EmployeeBase):
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    personnel_number: str | None = None
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    callsign: str | None = None
    is_active: bool | None = None


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
