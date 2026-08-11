from app.extensions import db
from app.models import Card, Child


def test_child_pin_hash_roundtrip(app):
    child = Child(first_name="Anna", last_name="Andersson")
    child.set_retrieval_pin("123456")
    db.session.add(child)
    db.session.commit()

    assert child.check_retrieval_pin("123456") is True
    assert child.check_retrieval_pin("000000") is False


def test_active_card_returns_only_active_one(app):
    child = Child(first_name="Bo", last_name="Berg")
    db.session.add(child)
    db.session.commit()

    old_card = Card(child=child, token="old-token")
    db.session.add(old_card)
    db.session.commit()
    old_card.revoke()

    new_card = Card(child=child, token="new-token")
    db.session.add(new_card)
    db.session.commit()

    assert child.active_card().token == "new-token"
