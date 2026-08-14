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


def test_is_adult_true_once_birth_year_plus_threshold_reached():
    child = Child(first_name="Ida", last_name="Ivarsson", birth_year=2006)
    assert child.is_adult(18, as_of_year=2024) is True
    assert child.is_adult(18, as_of_year=2023) is False


def test_is_adult_false_without_birth_year():
    child = Child(first_name="Jon", last_name="Jonsson")
    assert child.is_adult(18, as_of_year=2099) is False


def test_is_adult_disabled_when_threshold_is_zero():
    child = Child(first_name="Kim", last_name="Karlsson", birth_year=1990)
    assert child.is_adult(0, as_of_year=2099) is False
