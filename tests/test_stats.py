from datetime import datetime, timedelta, timezone

from app.admin import stats
from app.extensions import db
from app.models import LogEntry, Member


def _member(first_name):
    member = Member(first_name=first_name, last_name="Testsson")
    db.session.add(member)
    db.session.commit()
    return member


def _log(event_type, member_id, days_ago=0, hours_ago=0):
    entry = LogEntry(event_type=event_type, member_id=member_id, source="gate-scanner")
    entry.timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    db.session.add(entry)
    db.session.commit()
    return entry


def test_active_now_counts_only_checked_in_active_members(app):
    _member("Anna").current_status = "in"
    db.session.commit()
    out_member = _member("Bo")
    out_member.current_status = "out"
    db.session.commit()

    assert stats.active_now() == 1


def test_visits_by_day_zero_fills_and_counts_check_ins(app):
    member = _member("Cim")
    _log("check_in", member.id, days_ago=0)
    _log("check_in", member.id, days_ago=0)
    _log("check_in", member.id, days_ago=2)

    result = dict(stats.visits_by_day(days=5))
    assert len(result) == 5
    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert result[today_key] == 2


def test_visits_by_week_and_month_zero_fill(app):
    weeks = stats.visits_by_week(weeks=4)
    months = stats.visits_by_month(months=3)
    assert len(weeks) == 4
    assert len(months) == 3
    assert all(count == 0 for _, count in weeks)
    assert all(count == 0 for _, count in months)


def test_popular_hours_groups_by_hour_of_day(app):
    member = _member("Disa")
    now = datetime.now(timezone.utc)
    entry = LogEntry(event_type="check_in", member_id=member.id, source="gate-scanner")
    entry.timestamp = now.replace(hour=(now.hour), minute=0, second=0, microsecond=0)
    db.session.add(entry)
    db.session.commit()

    hours = dict(stats.popular_hours(days=1))
    assert len(hours) == 24
    assert hours[now.hour] == 1


def test_unique_visitors_counts_distinct_members(app):
    m1 = _member("Elin")
    m2 = _member("Filip")
    _log("check_in", m1.id)
    _log("check_in", m1.id)  # same member twice, shouldn't double count
    _log("check_in", m2.id)

    assert stats.unique_visitors(days=7) == 2


def test_unique_visitors_period_comparison(app):
    m1 = _member("Gustav")
    m2 = _member("Hanna")
    _log("check_in", m1.id, days_ago=1)  # current 7-day window
    _log("check_in", m2.id, days_ago=10)  # previous 7-day window

    current, previous = stats.unique_visitors_period_comparison(days=7)
    assert current == 1
    assert previous == 1


def test_average_visit_duration_pairs_check_in_and_out(app):
    member = _member("Ida")
    _log("check_in", member.id, hours_ago=2)
    _log("check_out", member.id, hours_ago=1)  # 60 minute visit

    avg = stats.average_visit_duration_minutes(days=7)
    assert avg is not None
    assert 55 <= avg <= 65


def test_average_visit_duration_none_without_complete_pair(app):
    member = _member("Jon")
    _log("check_in", member.id, hours_ago=1)  # never checked out

    assert stats.average_visit_duration_minutes(days=7) is None
