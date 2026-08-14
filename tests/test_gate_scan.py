from app.card.services import issue_card
from app.extensions import db
from app.models import LogEntry, Member


def _register_member(app, first_name="Gunnar"):
    member = Member(first_name=first_name, last_name="Gustafsson")
    db.session.add(member)
    db.session.commit()
    card = issue_card(member)
    db.session.commit()
    return member, card


def test_first_scan_checks_in(app, client):
    member, card = _register_member(app)

    response = client.post("/gate/scan", data={"token": card.token})
    payload = response.get_json()

    assert payload["status"] == "checked_in"
    assert payload["member_name"] == member.full_name()
    assert db.session.get(Member, member.id).current_status == "in"


def test_second_scan_checks_out(app, client):
    member, card = _register_member(app)
    app.config["SCAN_DEBOUNCE_SECONDS"] = 0

    client.post("/gate/scan", data={"token": card.token})
    response = client.post("/gate/scan", data={"token": card.token})
    payload = response.get_json()

    assert payload["status"] == "checked_out"
    assert db.session.get(Member, member.id).current_status == "out"


def test_unknown_token_is_rejected(client):
    response = client.post("/gate/scan", data={"token": "does-not-exist"})
    payload = response.get_json()

    assert payload["status"] == "rejected"
    log = LogEntry.query.filter_by(event_type="scan_rejected").first()
    assert log is not None


def test_debounce_prevents_immediate_double_toggle(app, client):
    member, card = _register_member(app)
    app.config["SCAN_DEBOUNCE_SECONDS"] = 10

    first = client.post("/gate/scan", data={"token": card.token}).get_json()
    second = client.post("/gate/scan", data={"token": card.token}).get_json()

    assert first["status"] == "checked_in"
    assert second["status"] == "debounced"
    assert db.session.get(Member, member.id).current_status == "in"


def test_revoked_card_is_rejected(app, client):
    member, card = _register_member(app)
    card.revoke()
    db.session.commit()

    response = client.post("/gate/scan", data={"token": card.token})
    assert response.get_json()["status"] == "rejected"
