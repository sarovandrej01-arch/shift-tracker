from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo("Europe/Moscow")


def business_today(moment: datetime | None = None) -> date:
    current = moment if moment is not None else datetime.now(BUSINESS_TIMEZONE)
    if current.tzinfo is None or current.utcoffset() is None:
        current = current.replace(tzinfo=BUSINESS_TIMEZONE)
    return current.astimezone(BUSINESS_TIMEZONE).date()


def utc_day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def utc_day_end_exclusive(value: date) -> datetime:
    return datetime.combine(value + timedelta(days=1), time.min, tzinfo=timezone.utc)
