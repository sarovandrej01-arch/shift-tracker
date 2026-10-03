from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_dashboard_service, require_moderator_or_admin
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryRead
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryRead)
async def dashboard_summary(
    date_from: date | None = Query(
        default=None,
        description=(
            "Inclusive start of the period. Messages use created_at UTC day bounds. "
            "Shifts use shift_date. If both date_from and date_to are omitted, both "
            "become the current calendar date in Europe/Moscow."
        ),
    ),
    date_to: date | None = Query(
        default=None,
        description=(
            "Inclusive end of the period. Messages use created_at UTC day bounds. "
            "Shifts use shift_date. If both bounds are omitted, the period is today "
            "in Europe/Moscow."
        ),
    ),
    object_id: int | None = Query(default=None, description="Limit counts to one work object"),
    _: User = Depends(require_moderator_or_admin),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryRead:
    """Summary of messages and shifts.

    Message counts use TelegramMessage.created_at with inclusive UTC calendar dates.
    Shift counts use Shift.shift_date. These are different dates and are not mixed.
    When both date_from and date_to are omitted, the period is the current calendar
    date in Europe/Moscow, the default work-object timezone.
    """
    return await service.summary(date_from=date_from, date_to=date_to, object_id=object_id)
