from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import utc_day_end_exclusive, utc_day_start
from app.core.enums import MessageStatus
from app.models.shift import Shift
from app.models.telegram_message import TelegramMessage
from app.models.work_object import WorkObject


@dataclass(slots=True)
class MessageStatusCounts:
    total: int
    new: int
    processing: int
    accepted: int
    review: int
    rejected: int
    duplicate: int
    error: int


@dataclass(slots=True)
class ShiftConfirmationCounts:
    total: int
    automatic: int
    manual: int


@dataclass(slots=True)
class ObjectMessageCounts:
    object_id: int
    messages_total: int
    accepted: int
    review: int
    rejected: int


@dataclass(slots=True)
class ObjectShiftCounts:
    object_id: int
    shifts_total: int


def _status_count(status: MessageStatus):
    return func.count(TelegramMessage.id).filter(TelegramMessage.status == status)


def _apply_message_period(stmt, *, date_from: date | None, date_to: date | None, object_id: int | None):
    if date_from is not None:
        stmt = stmt.where(TelegramMessage.created_at >= utc_day_start(date_from))
    if date_to is not None:
        stmt = stmt.where(TelegramMessage.created_at < utc_day_end_exclusive(date_to))
    if object_id is not None:
        stmt = stmt.where(TelegramMessage.object_id == object_id)
    return stmt


def _apply_shift_period(stmt, *, date_from: date | None, date_to: date | None, object_id: int | None):
    if date_from is not None:
        stmt = stmt.where(Shift.shift_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Shift.shift_date <= date_to)
    if object_id is not None:
        stmt = stmt.where(Shift.object_id == object_id)
    return stmt


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def message_status_counts(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        object_id: int | None = None,
    ) -> MessageStatusCounts:
        stmt = select(
            func.count(TelegramMessage.id).label("total"),
            _status_count(MessageStatus.NEW).label("new"),
            _status_count(MessageStatus.PROCESSING).label("processing"),
            _status_count(MessageStatus.ACCEPTED).label("accepted"),
            _status_count(MessageStatus.REVIEW).label("review"),
            _status_count(MessageStatus.REJECTED).label("rejected"),
            _status_count(MessageStatus.DUPLICATE).label("duplicate"),
            _status_count(MessageStatus.ERROR).label("error"),
        )
        stmt = _apply_message_period(stmt, date_from=date_from, date_to=date_to, object_id=object_id)
        row = (await self.session.execute(stmt)).one()
        return MessageStatusCounts(
            total=row.total,
            new=row.new,
            processing=row.processing,
            accepted=row.accepted,
            review=row.review,
            rejected=row.rejected,
            duplicate=row.duplicate,
            error=row.error,
        )

    async def shift_confirmation_counts(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        object_id: int | None = None,
    ) -> ShiftConfirmationCounts:
        stmt = select(
            func.count(Shift.id).label("total"),
            func.count(Shift.id).filter(Shift.confirmed_manually.is_(False)).label("automatic"),
            func.count(Shift.id).filter(Shift.confirmed_manually.is_(True)).label("manual"),
        )
        stmt = _apply_shift_period(stmt, date_from=date_from, date_to=date_to, object_id=object_id)
        row = (await self.session.execute(stmt)).one()
        return ShiftConfirmationCounts(total=row.total, automatic=row.automatic, manual=row.manual)

    async def message_counts_by_object(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        object_id: int | None = None,
    ) -> list[ObjectMessageCounts]:
        stmt = (
            select(
                TelegramMessage.object_id,
                func.count(TelegramMessage.id).label("messages_total"),
                _status_count(MessageStatus.ACCEPTED).label("accepted"),
                _status_count(MessageStatus.REVIEW).label("review"),
                _status_count(MessageStatus.REJECTED).label("rejected"),
            )
            .where(TelegramMessage.object_id.is_not(None))
            .group_by(TelegramMessage.object_id)
        )
        stmt = _apply_message_period(stmt, date_from=date_from, date_to=date_to, object_id=object_id)
        rows = (await self.session.execute(stmt)).all()
        return [
            ObjectMessageCounts(
                object_id=row.object_id,
                messages_total=row.messages_total,
                accepted=row.accepted,
                review=row.review,
                rejected=row.rejected,
            )
            for row in rows
            if row.object_id is not None
        ]

    async def shift_counts_by_object(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        object_id: int | None = None,
    ) -> list[ObjectShiftCounts]:
        stmt = (
            select(
                Shift.object_id,
                func.count(Shift.id).label("shifts_total"),
            )
            .group_by(Shift.object_id)
        )
        stmt = _apply_shift_period(stmt, date_from=date_from, date_to=date_to, object_id=object_id)
        rows = (await self.session.execute(stmt)).all()
        return [
            ObjectShiftCounts(object_id=row.object_id, shifts_total=row.shifts_total)
            for row in rows
        ]

    async def object_names(self, object_ids: list[int]) -> dict[int, str]:
        if not object_ids:
            return {}
        stmt = select(WorkObject.id, WorkObject.name).where(WorkObject.id.in_(object_ids))
        rows = (await self.session.execute(stmt)).all()
        return {row.id: row.name for row in rows}
