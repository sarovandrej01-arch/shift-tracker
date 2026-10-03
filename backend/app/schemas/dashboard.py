from datetime import date

from pydantic import BaseModel, Field


class DashboardPeriodRead(BaseModel):
    date_from: date | None
    date_to: date | None


class DashboardMessageCounts(BaseModel):
    total: int
    new: int = 0
    processing: int = 0
    accepted: int
    review: int
    rejected: int
    duplicate: int
    error: int


class DashboardShiftCounts(BaseModel):
    total: int
    automatic: int
    manual: int


class DashboardObjectSummary(BaseModel):
    object_id: int
    object_name: str
    messages_total: int
    accepted: int
    review: int
    rejected: int
    shifts_total: int


class DashboardSummaryRead(BaseModel):
    period: DashboardPeriodRead
    messages: DashboardMessageCounts
    shifts: DashboardShiftCounts
    by_object: list[DashboardObjectSummary] = Field(default_factory=list)
