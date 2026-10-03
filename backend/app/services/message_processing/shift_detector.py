from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.work_object import WorkObject


class ShiftDetectionStatus(str, Enum):
    MATCHED = "matched"
    OUTSIDE_WINDOW = "outside_window"


@dataclass(slots=True)
class ShiftDetectionResult:
    status: ShiftDetectionStatus
    shift_date: date | None
    message_local_datetime: datetime
    shift_start_datetime: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None


@dataclass(slots=True)
class _ShiftWindow:
    shift_date: date
    shift_start: datetime
    window_start: datetime
    window_end: datetime


class ShiftDetector:
    def detect(
        self,
        *,
        message_datetime: datetime,
        work_object: WorkObject,
    ) -> ShiftDetectionResult:
        if message_datetime.tzinfo is None or message_datetime.utcoffset() is None:
            raise ValueError("message_datetime must be timezone-aware")
        if work_object.checkin_before_minutes < 0:
            raise ValueError("checkin_before_minutes must be >= 0")
        if work_object.checkin_after_minutes < 0:
            raise ValueError("checkin_after_minutes must be >= 0")

        try:
            tz = ZoneInfo(work_object.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid work object timezone") from exc

        message_local = message_datetime.astimezone(tz)
        matches = [
            window
            for window in self._candidate_windows(message_local.date(), work_object.shift_start_time, tz, work_object)
            if window.window_start <= message_local <= window.window_end
        ]
        if not matches:
            return ShiftDetectionResult(
                status=ShiftDetectionStatus.OUTSIDE_WINDOW,
                shift_date=None,
                message_local_datetime=message_local,
            )

        best = min(
            matches,
            key=lambda item: (
                abs((message_local - item.shift_start).total_seconds()),
                item.shift_date,
            ),
        )
        return ShiftDetectionResult(
            status=ShiftDetectionStatus.MATCHED,
            shift_date=best.shift_date,
            message_local_datetime=message_local,
            shift_start_datetime=best.shift_start,
            window_start=best.window_start,
            window_end=best.window_end,
        )

    def _candidate_windows(
        self,
        local_date: date,
        shift_start_time: time,
        tz: ZoneInfo,
        work_object: WorkObject,
    ) -> list[_ShiftWindow]:
        windows: list[_ShiftWindow] = []
        for candidate_date in (
            local_date - timedelta(days=1),
            local_date,
            local_date + timedelta(days=1),
        ):
            shift_start = datetime.combine(candidate_date, shift_start_time, tzinfo=tz)
            windows.append(
                _ShiftWindow(
                    shift_date=candidate_date,
                    shift_start=shift_start,
                    window_start=shift_start - timedelta(minutes=work_object.checkin_before_minutes),
                    window_end=shift_start + timedelta(minutes=work_object.checkin_after_minutes),
                )
            )
        return windows
