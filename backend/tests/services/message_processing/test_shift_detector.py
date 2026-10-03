from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.services.message_processing import ShiftDetectionStatus, ShiftDetector

MOSCOW = ZoneInfo("Europe/Moscow")
UTC = ZoneInfo("UTC")


class FakeWorkObject:
    def __init__(
        self,
        shift_start_time: time,
        checkin_before_minutes: int,
        checkin_after_minutes: int,
        timezone: str = "Europe/Moscow",
    ) -> None:
        self.shift_start_time = shift_start_time
        self.checkin_before_minutes = checkin_before_minutes
        self.checkin_after_minutes = checkin_after_minutes
        self.timezone = timezone


def test_day_shift_inside_window() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 9, 30, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(9, 0), 60, 120),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()


def test_before_start_but_inside_window() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 8, 15, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(9, 0), 60, 120),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()


def test_after_window() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 11, 30, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(9, 0), 60, 120),
    )

    assert result.status is ShiftDetectionStatus.OUTSIDE_WINDOW
    assert result.shift_date is None


def test_night_shift_after_midnight_belongs_to_previous_date() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 3, 0, 30, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()
    assert result.shift_start_datetime == datetime(2026, 10, 2, 20, 0, tzinfo=MOSCOW)
    assert result.window_start == datetime(2026, 10, 2, 19, 0, tzinfo=MOSCOW)
    assert result.window_end == datetime(2026, 10, 3, 1, 0, tzinfo=MOSCOW)


def test_exact_window_start_is_included() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 19, 0, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()


def test_exact_window_end_is_included() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 3, 1, 0, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()


def test_one_second_before_window() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 18, 59, 59, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.OUTSIDE_WINDOW
    assert result.shift_date is None


def test_one_second_after_window() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 3, 1, 0, 1, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.OUTSIDE_WINDOW
    assert result.shift_date is None


def test_utc_input_is_converted_to_object_timezone() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 17, 30, tzinfo=UTC),
        work_object=FakeWorkObject(time(20, 0), 60, 300),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()
    assert result.message_local_datetime == datetime(2026, 10, 2, 20, 30, tzinfo=MOSCOW)
    assert result.message_local_datetime.tzinfo == MOSCOW


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ShiftDetector().detect(
            message_datetime=datetime(2026, 10, 2, 20, 30),
            work_object=FakeWorkObject(time(20, 0), 60, 300),
        )


def test_invalid_timezone_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid work object timezone"):
        ShiftDetector().detect(
            message_datetime=datetime(2026, 10, 2, 20, 30, tzinfo=UTC),
            work_object=FakeWorkObject(time(20, 0), 60, 300, timezone="Invalid/Timezone"),
        )


def test_negative_checkin_before_is_rejected() -> None:
    with pytest.raises(ValueError, match="checkin_before_minutes"):
        ShiftDetector().detect(
            message_datetime=datetime(2026, 10, 2, 20, 30, tzinfo=MOSCOW),
            work_object=FakeWorkObject(time(20, 0), -1, 300),
        )


def test_negative_checkin_after_is_rejected() -> None:
    with pytest.raises(ValueError, match="checkin_after_minutes"):
        ShiftDetector().detect(
            message_datetime=datetime(2026, 10, 2, 20, 30, tzinfo=MOSCOW),
            work_object=FakeWorkObject(time(20, 0), 60, -1),
        )


def test_overlapping_windows_choose_nearest_shift_start() -> None:
    result = ShiftDetector().detect(
        message_datetime=datetime(2026, 10, 2, 21, 0, tzinfo=MOSCOW),
        work_object=FakeWorkObject(time(12, 0), 18 * 60, 18 * 60),
    )

    assert result.status is ShiftDetectionStatus.MATCHED
    assert result.shift_date == datetime(2026, 10, 2).date()
    assert result.shift_start_datetime == datetime(2026, 10, 2, 12, 0, tzinfo=MOSCOW)
