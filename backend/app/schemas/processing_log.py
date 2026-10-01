from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProcessingLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    user_id: int | None
    action: str
    details: str | None
    created_at: datetime
