from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class WorkObjectBase(BaseModel):
    name: str
    shift_start_time: time
    checkin_before_minutes: int = Field(ge=0)
    checkin_after_minutes: int = Field(ge=0)
    timezone: str = "Europe/Moscow"


class WorkObjectCreate(WorkObjectBase):
    is_active: bool = True


class WorkObjectUpdate(BaseModel):
    name: str | None = None
    shift_start_time: time | None = None
    checkin_before_minutes: int | None = Field(default=None, ge=0)
    checkin_after_minutes: int | None = Field(default=None, ge=0)
    timezone: str | None = None
    is_active: bool | None = None


class WorkObjectRead(WorkObjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
