from datetime import datetime, timedelta, timezone

from app.admin.services import purge_children_who_turned_adult
from app.card.services import auto_checkout_all, issue_card
from app.extensions import db
from app.models import Child, GuardianContact, LogEntry
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


def test_purge_children_who_turned_adult_erases_only_adults(app):
    this_year = datetime.now(timezone.utc).year

    adult = Child(first_name="Liv", last_name="Larsson", birth_year=this_year - 18, active=True)
    adult.set_retrieval_pin("111111")
    db.session.add(adult)
    db.session.add(GuardianContact(child=adult, name="Vårdnadshavare Liv"))
    db.session.commit()
    issue_card(adult)
    db.session.commit()

    minor = Child(first_name="Moa", last_name="Malm", birth_year=this_year - 10, active=True)
    db.session.add(minor)
    db.session.commit()

    erased = purge_children_who_turned_adult(18)

    assert erased == 1

    refreshed_adult = db.session.get(Child, adult.id)
    assert refreshed_adult.active is False
    assert refreshed_adult.first_name == "Raderad"
    assert refreshed_adult.guardians == []
    assert refreshed_adult.active_card() is None
    assert LogEntry.query.filter_by(event_type="child_data_deleted", child_id=adult.id).first() is not None

    refreshed_minor = db.session.get(Child, minor.id)
    assert refreshed_minor.active is True
    assert refreshed_minor.first_name == "Moa"


def test_purge_children_who_turned_adult_disabled_when_threshold_is_zero(app):
    this_year = datetime.now(timezone.utc).year
    adult = Child(first_name="Nils", last_name="Nyberg", birth_year=this_year - 40, active=True)
    db.session.add(adult)
    db.session.commit()

    erased = purge_children_who_turned_adult(0)

    assert erased == 0
    assert db.session.get(Child, adult.id).active is True
