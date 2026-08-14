from app.admin.services import register_member
from app.card.routes import REMEMBER_COOKIE_NAME
from app.extensions import db
from app.models import Member


def test_join_sets_remember_cookie(client):
    response = client.post("/join", data={"first_name": "Elin", "last_name": "Ekstrom"})
    assert response.status_code == 200
    assert REMEMBER_COOKIE_NAME in response.headers.get("Set-Cookie", "")


def test_gate_tap_without_cookie_redirects_to_retrieve(client):
    response = client.get("/gate/tap")
    assert response.status_code == 302
    assert "/card/retrieve" in response.headers["Location"]
    assert "next=" in response.headers["Location"]


def test_gate_tap_with_cookie_checks_in(client):
    client.post("/join", data={"first_name": "Filip", "last_name": "Falk"})
    member = Member.query.filter_by(first_name="Filip").first()

    response = client.get("/gate/tap")
    assert response.status_code == 200
    assert "incheckad".encode() in response.data
    assert db.session.get(Member, member.id).current_status == "in"


def test_gate_tap_with_unknown_cookie_shows_error(client):
    client.set_cookie(REMEMBER_COOKIE_NAME, "does-not-exist")
    response = client.get("/gate/tap")
    assert response.status_code == 200
    assert "Identifiera dig igen".encode() in response.data


def test_retrieve_with_next_sets_cookie_and_redirects(app, client):
    result = register_member(first_name="Gustav", last_name="Gren", source="web-app")
    # simulate a fresh browser: no "remember me" cookie yet
    client.delete_cookie(REMEMBER_COOKIE_NAME)

    response = client.post(
        "/card/retrieve",
        data={"first_name": "Gustav", "last_name": "Gren", "pin": result.raw_pin, "next": "/gate/tap"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/gate/tap"
    assert REMEMBER_COOKIE_NAME in response.headers.get("Set-Cookie", "")


def test_retrieve_without_next_shows_qr_page(client):
    result = register_member(first_name="Hanna", last_name="Holm", source="web-app")

    response = client.post(
        "/card/retrieve", data={"first_name": "Hanna", "last_name": "Holm", "pin": result.raw_pin}
    )
    assert response.status_code == 200
    assert "Hanna Holm".encode() in response.data
