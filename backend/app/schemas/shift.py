from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    object_id: int
    shift_date: date
    source_message_id: int | None
    confirmed_manually: bool
    confirmed_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
