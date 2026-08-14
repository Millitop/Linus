"""Aggregate statistics for the admin dashboard.

Deliberately query-only (no browsable member listing lives here -- see
app/admin/routes.py::members_search for the search-only lookup). Uses
SQLite's strftime() directly since this project only ever targets
SQLite (see docs/architecture.md) -- no need for a database-agnostic
abstraction.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.extensions import db
from app.models import LogEntry, Member


def active_now() -> int:
    return Member.query.filter_by(current_status="in", active=True).count()


def visits_by_day(days: int = 14) -> list[tuple[str, int]]:
    """Number of check_in events per calendar day for the last ``days``
    days, oldest first, with zero-filled gaps so a chart doesn't skip
    days with no visits.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.session.query(
            func.strftime("%Y-%m-%d", LogEntry.timestamp).label("day"),
            func.count(LogEntry.id),
        )
        .filter(LogEntry.event_type == "check_in", LogEntry.timestamp >= since)
        .group_by("day")
        .all()
    )
    counts = dict(rows)

    result = []
    for offset in range(days - 1, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=offset)).strftime("%Y-%m-%d")
        result.append((day, counts.get(day, 0)))
    return result


def popular_hours(days: int = 30) -> list[tuple[int, int]]:
    """Number of check_in events per hour-of-day (0-23) over the last
    ``days`` days, for spotting the busiest times to staff for.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.session.query(
            func.strftime("%H", LogEntry.timestamp).label("hour"),
            func.count(LogEntry.id),
        )
        .filter(LogEntry.event_type == "check_in", LogEntry.timestamp >= since)
        .group_by("hour")
        .all()
    )
    counts = {int(hour): count for hour, count in rows}
    return [(hour, counts.get(hour, 0)) for hour in range(24)]


def unique_visitors(days: int = 30) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.session.query(func.count(func.distinct(LogEntry.member_id)))
        .filter(LogEntry.event_type == "check_in", LogEntry.timestamp >= since)
        .scalar()
        or 0
    )
