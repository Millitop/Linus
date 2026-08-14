from datetime import datetime, timedelta, timezone

from app.admin.services import purge_inactive_members
from app.card.services import auto_checkout_all, issue_card
from app.extensions import db
from app.models import EmergencyContact, LogEntry, Member
from scripts.retention_cleanup import purge_old_logs


def test_auto_checkout_all_resets_everyone_checked_in(app):
    member = Member(first_name="Hanna", last_name="Holm", current_status="in")
    db.session.add(member)
    db.session.commit()
    issue_card(member)
    db.session.commit()

    count = auto_checkout_all()

    assert count == 1
    assert db.session.get(Member, member.id).current_status == "out"


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


def _member_with_last_activity(first_name, days_ago, active=True):
    member = Member(first_name=first_name, last_name="Testsson", active=active)
    member.set_retrieval_pin("111111")
    db.session.add(member)
    db.session.add(EmergencyContact(member=member, name=f"Kontakt {first_name}"))
    db.session.commit()
    issue_card(member)
    entry = LogEntry(event_type="check_in", member_id=member.id, source="gate-scanner")
    entry.timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.session.add(entry)
    db.session.commit()
    return member


def test_purge_inactive_members_erases_only_the_inactive_one(app):
    inactive = _member_with_last_activity("Liv", days_ago=400)
    active_recent = _member_with_last_activity("Moa", days_ago=5)

    erased = purge_inactive_members(12)

    assert erased == 1

    refreshed_inactive = db.session.get(Member, inactive.id)
    assert refreshed_inactive.active is False
    assert refreshed_inactive.first_name == "Raderad"
    assert refreshed_inactive.emergency_contacts == []
    assert refreshed_inactive.active_card() is None
    deletion_log = LogEntry.query.filter_by(event_type="member_data_deleted", member_id=inactive.id).first()
    assert deletion_log is not None

    refreshed_active = db.session.get(Member, active_recent.id)
    assert refreshed_active.active is True
    assert refreshed_active.first_name == "Moa"


def test_purge_inactive_members_uses_registration_date_if_never_checked_in(app):
    member = Member(first_name="Nils", last_name="Nyberg", active=True)
    db.session.add(member)
    db.session.commit()
    member.created_at = datetime.now(timezone.utc) - timedelta(days=400)
    db.session.commit()

    erased = purge_inactive_members(12)

    assert erased == 1
    assert db.session.get(Member, member.id).active is False


def test_purge_inactive_members_disabled_when_threshold_is_zero(app):
    inactive = _member_with_last_activity("Ove", days_ago=9999)

    erased = purge_inactive_members(0)

    assert erased == 0
    assert db.session.get(Member, inactive.id).active is True
