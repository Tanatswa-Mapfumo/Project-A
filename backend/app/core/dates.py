"""Date/time helpers.

All timestamps are stored in UTC. The user's local calendar date is derived from the
optional `profiles.timezone` column (IANA name, default UTC). Never rely on the
server-local timezone.
"""

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings


def resolve_timezone(tz_name: str | None) -> ZoneInfo:
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            pass
    return ZoneInfo(settings.default_timezone)


def local_date(tz_name: str | None, now: dt.datetime | None = None) -> dt.date:
    now = now or dt.datetime.now(dt.UTC)
    return now.astimezone(resolve_timezone(tz_name)).date()


def parse_iso_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def week_start_of(day: dt.date) -> dt.date:
    """Monday-start ISO week containing `day`."""
    return day - dt.timedelta(days=day.weekday())


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    days: list[dt.date] = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += dt.timedelta(days=1)
    return days
