"""WAT is UTC+1, fixed offset, no DST. All arithmetic is done in UTC then
converted to WAT for display, so date rollovers (e.g. 23:50 UTC -> 00:50 WAT
next day) are handled correctly by construction rather than by hand."""
from datetime import datetime, timedelta, timezone

WAT_OFFSET = timedelta(hours=1)


def parse_utc(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def to_wat(dt_utc: datetime) -> datetime:
    return dt_utc + WAT_OFFSET


def fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_wat(dt_utc: datetime) -> str:
    return to_wat(dt_utc).strftime("%Y-%m-%d %H:%M WAT")


def add_hours(dt_utc: datetime, hours: float) -> datetime:
    return dt_utc + timedelta(hours=hours)


def add_calendar_days(dt_utc: datetime, days: float) -> datetime:
    return dt_utc + timedelta(days=days)
