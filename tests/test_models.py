from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import Card, LogEntry, Member


def test_member_pin_hash_roundtrip(app):
    member = Member(first_name="Anna", last_name="Andersson")
    member.set_retrieval_pin("123456")
    db.session.add(member)
    db.session.commit()

    assert member.check_retrieval_pin("123456") is True
    assert member.check_retrieval_pin("000000") is False


def test_active_card_returns_only_active_one(app):
    member = Member(first_name="Bo", last_name="Berg")
    db.session.add(member)
    db.session.commit()

    old_card = Card(member=member, token="old-token")
    db.session.add(old_card)
    db.session.commit()
    old_card.revoke()

    new_card = Card(member=member, token="new-token")
    db.session.add(new_card)
    db.session.commit()

    assert member.active_card().token == "new-token"


def test_last_activity_at_uses_most_recent_check_in_or_out(app):
    member = Member(first_name="Cim", last_name="Carlsson")
    db.session.add(member)
    db.session.commit()

    old_entry = LogEntry(event_type="check_in", member_id=member.id)
    old_entry.timestamp = datetime.now(timezone.utc) - timedelta(days=10)
    recent_entry = LogEntry(event_type="check_out", member_id=member.id)
    recent_entry.timestamp = datetime.now(timezone.utc) - timedelta(days=1)
    db.session.add_all([old_entry, recent_entry])
    db.session.commit()

    last_activity = member.last_activity_at()
    assert abs((last_activity - recent_entry.timestamp).total_seconds()) < 1


def test_last_activity_at_falls_back_to_created_at_without_check_ins(app):
    member = Member(first_name="Disa", last_name="Dahl")
    db.session.add(member)
    db.session.commit()

    assert member.last_activity_at() == member.created_at
