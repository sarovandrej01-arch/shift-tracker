from collections.abc import Callable
from datetime import date

from app.core.dates import business_today
from app.core.query_validation import ensure_date_order
from app.repositories.dashboard.repository import DashboardRepository
from app.schemas.dashboard import (
    DashboardMessageCounts,
    DashboardObjectSummary,
    DashboardPeriodRead,
    DashboardShiftCounts,
    DashboardSummaryRead,
)


class DashboardService:
    def __init__(
        self,
        repository: DashboardRepository,
        *,
        today: Callable[[], date] | None = None,
    ) -> None:
        self.repository = repository
        self.today = today or business_today

    async def summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        object_id: int | None = None,
    ) -> DashboardSummaryRead:
        if date_from is None and date_to is None:
            current = self.today()
            date_from = current
            date_to = current
        ensure_date_order(date_from, date_to)
        messages = await self.repository.message_status_counts(
            date_from=date_from,
            date_to=date_to,
            object_id=object_id,
        )
        shifts = await self.repository.shift_confirmation_counts(
            date_from=date_from,
            date_to=date_to,
            object_id=object_id,
        )
        message_rows = await self.repository.message_counts_by_object(
            date_from=date_from,
            date_to=date_to,
            object_id=object_id,
        )
        shift_rows = await self.repository.shift_counts_by_object(
            date_from=date_from,
            date_to=date_to,
            object_id=object_id,
        )
        object_ids = sorted({row.object_id for row in message_rows} | {row.object_id for row in shift_rows})
        names = await self.repository.object_names(object_ids)
        messages_by_object = {row.object_id: row for row in message_rows}
        shifts_by_object = {row.object_id: row for row in shift_rows}
        return DashboardSummaryRead(
            period=DashboardPeriodRead(date_from=date_from, date_to=date_to),
            messages=DashboardMessageCounts(
                total=messages.total,
                new=messages.new,
                processing=messages.processing,
                accepted=messages.accepted,
                review=messages.review,
                rejected=messages.rejected,
                duplicate=messages.duplicate,
                error=messages.error,
            ),
            shifts=DashboardShiftCounts(
                total=shifts.total,
                automatic=shifts.automatic,
                manual=shifts.manual,
            ),
            by_object=[
                DashboardObjectSummary(
                    object_id=object_id_value,
                    object_name=names.get(object_id_value, ""),
                    messages_total=messages_by_object[object_id_value].messages_total
                    if object_id_value in messages_by_object
                    else 0,
                    accepted=messages_by_object[object_id_value].accepted
                    if object_id_value in messages_by_object
                    else 0,
                    review=messages_by_object[object_id_value].review
                    if object_id_value in messages_by_object
                    else 0,
                    rejected=messages_by_object[object_id_value].rejected
                    if object_id_value in messages_by_object
                    else 0,
                    shifts_total=shifts_by_object[object_id_value].shifts_total
                    if object_id_value in shifts_by_object
                    else 0,
                )
                for object_id_value in object_ids
            ],
        )
