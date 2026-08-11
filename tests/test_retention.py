from datetime import datetime, timedelta, timezone

from app.card.services import auto_checkout_all, issue_card
from app.extensions import db
from app.models import Child, LogEntry
from scripts.retention_cleanup import purge_old_logs


def test_auto_checkout_all_resets_everyone_checked_in(app):
    child = Child(first_name="Hanna", last_name="Holm", current_status="in")
    db.session.add(child)
    db.session.commit()
    issue_card(child)
    db.session.commit()

    count = auto_checkout_all()

    assert count == 1
    assert db.session.get(Child, child.id).current_status == "out"


def test_purge_old_logs_removes_entries_past_retention(app):
    old_entry = LogEntry(event_type="check_in", source="gate-scanner")
    old_entry.timestamp = datetime.now(timezone.utc) - timedelta(days=400)
    recent_entry = LogEntry(event_type="check_in", source="gate-scanner")

    db.session.add_all([old_entry, recent_entry])
    db.session.commit()

    deleted = purge_old_logs(retention_days=365)

    assert deleted == 1
    assert LogEntry.query.count() == 1


def test_purge_disabled_when_retention_days_is_zero(app):
    entry = LogEntry(event_type="check_in", source="gate-scanner")
    entry.timestamp = datetime.now(timezone.utc) - timedelta(days=9999)
    db.session.add(entry)
    db.session.commit()

    deleted = purge_old_logs(retention_days=0)

    assert deleted == 0
    assert LogEntry.query.count() == 1
