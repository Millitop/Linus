"""Aggregate statistics for the admin dashboard.

Deliberately query-only (no browsable member listing lives here -- see
app/admin/routes.py::members_search for the search-only lookup). Uses
SQLite's strftime() directly since this project only ever targets
SQLite (see docs/architecture.md) -- no need for a database-agnostic
abstraction.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

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


def visits_by_week(weeks: int = 12) -> list[tuple[str, int]]:
    """Number of check_in events per ISO-ish week (year + week-of-year)
    for the last ``weeks`` weeks, oldest first, zero-filled. For longer
    trends than visits_by_day is meant to show.
    """
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    rows = (
        db.session.query(
            func.strftime("%Y-W%W", LogEntry.timestamp).label("week"),
            func.count(LogEntry.id),
        )
        .filter(LogEntry.event_type == "check_in", LogEntry.timestamp >= since)
        .group_by("week")
        .all()
    )
    counts = dict(rows)

    result = []
    for offset in range(weeks - 1, -1, -1):
        week_start = datetime.now(timezone.utc) - timedelta(weeks=offset)
        key = week_start.strftime("%Y-W%W")
        result.append((key, counts.get(key, 0)))
    return result


def visits_by_month(months: int = 12) -> list[tuple[str, int]]:
    """Number of check_in events per calendar month for the last
    ``months`` months, oldest first, zero-filled.
    """
    since = datetime.now(timezone.utc) - timedelta(days=months * 31)
    rows = (
        db.session.query(
            func.strftime("%Y-%m", LogEntry.timestamp).label("month"),
            func.count(LogEntry.id),
        )
        .filter(LogEntry.event_type == "check_in", LogEntry.timestamp >= since)
        .group_by("month")
        .all()
    )
    counts = dict(rows)

    result = []
    today = datetime.now(timezone.utc)
    for offset in range(months - 1, -1, -1):
        year, month = today.year, today.month - offset
        while month <= 0:
            month += 12
            year -= 1
        key = f"{year:04d}-{month:02d}"
        result.append((key, counts.get(key, 0)))
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


def unique_visitors_period_comparison(days: int = 7) -> tuple[int, int]:
    """(current_period, previous_period) unique visitor counts for two
    consecutive windows of ``days`` days each -- e.g. this week vs last
    week, for spotting trends at a glance on the dashboard.
    """
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=days)
    previous_start = now - timedelta(days=days * 2)

    def _count(start: datetime, end: datetime) -> int:
        return (
            db.session.query(func.count(func.distinct(LogEntry.member_id)))
            .filter(
                LogEntry.event_type == "check_in",
                LogEntry.timestamp >= start,
                LogEntry.timestamp < end,
            )
            .scalar()
            or 0
        )

    return _count(current_start, now), _count(previous_start, current_start)


def average_visit_duration_minutes(days: int = 30) -> Optional[float]:
    """Average minutes between a check_in and its following check_out
    over the last ``days`` days. Returns None if there isn't a single
    complete pair yet.

    Computed in Python from a simple ordered query rather than SQL --
    pairing "this row with its matching next row per group" is awkward
    in SQLite and a small loop is easier to read and test.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    entries = (
        LogEntry.query.filter(
            LogEntry.event_type.in_(["check_in", "check_out"]),
            LogEntry.timestamp >= since,
        )
        .order_by(LogEntry.member_id, LogEntry.timestamp)
        .all()
    )

    open_check_ins: dict[int, datetime] = {}
    durations_minutes: list[float] = []
    for entry in entries:
        if entry.event_type == "check_in":
            open_check_ins[entry.member_id] = entry.timestamp
        elif entry.event_type == "check_out":
            start = open_check_ins.pop(entry.member_id, None)
            if start is not None:
                durations_minutes.append((entry.timestamp - start).total_seconds() / 60)

    if not durations_minutes:
        return None
    return sum(durations_minutes) / len(durations_minutes)
