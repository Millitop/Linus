from app.extensions import db
from app.models import LogEntry, Member


def _register_test_member(client, first_name="Olle"):
    client.post(
        "/admin/register",
        data={"first_name": first_name, "last_name": "Olsson", "phone": "0709998877"},
        follow_redirects=True,
    )
    return Member.query.filter_by(first_name=first_name).first()


def test_dashboard_has_no_browsable_member_list(logged_in_client):
    _register_test_member(logged_in_client)
    response = logged_in_client.get("/admin/")
    assert response.status_code == 200
    assert b"Olle Olsson" not in response.data
    assert "Statistik".encode() in response.data


def test_member_search_finds_registered_member_by_name(logged_in_client):
    _register_test_member(logged_in_client)

    empty = logged_in_client.get("/admin/members/search")
    assert b"Olle Olsson" not in empty.data

    found = logged_in_client.get("/admin/members/search?query=Olle")
    assert b"Olle Olsson" in found.data


def test_edit_member_updates_fields_and_logs_event(logged_in_client):
    member = _register_test_member(logged_in_client)

    response = logged_in_client.post(
        f"/admin/members/{member.id}/edit",
        data={"first_name": "Olle", "last_name": "Olsson-Andersson", "phone": "0709998877"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    updated = db.session.get(Member, member.id)
    assert updated.last_name == "Olsson-Andersson"
    assert LogEntry.query.filter_by(event_type="member_updated", member_id=member.id).first() is not None


def test_edit_member_requires_login(client):
    response = client.get("/admin/members/1/edit", follow_redirects=True)
    assert response.status_code == 200
    assert "Logga in".encode() in response.data


def test_delete_member_erases_personal_data(logged_in_client):
    member = _register_test_member(logged_in_client)

    response = logged_in_client.post(f"/admin/members/{member.id}/delete", follow_redirects=True)
    assert response.status_code == 200

    erased = db.session.get(Member, member.id)
    assert erased.active is False
    assert erased.first_name == "Raderad"
    assert erased.emergency_contacts == []
