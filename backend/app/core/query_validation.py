from datetime import date, datetime

from app.core.exceptions.query import InvalidDateRangeError


def ensure_date_order(
    start: date | datetime | None,
    end: date | datetime | None,
    *,
    start_name: str = "date_from",
    end_name: str = "date_to",
) -> None:
    if start is not None and end is not None and start > end:
        raise InvalidDateRangeError(f"{start_name} must be less than or equal to {end_name}")


def ensure_aware_datetime(value: datetime | None, name: str) -> None:
    if value is None:
        return
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidDateRangeError(f"{name} must be timezone-aware")
