from app.extensions import db
from app.models import Child, LogEntry


def _register_test_child(client, first_name="Olle"):
    client.post(
        "/admin/register",
        data={
            "first_name": first_name,
            "last_name": "Olsson",
            "group_class": "Grupp 2",
            "birth_year": "2017",
            "guardian_name": "Ove Olsson",
            "guardian_phone": "0709998877",
            "guardian_email": "ove@example.com",
        },
        follow_redirects=True,
    )
    return Child.query.filter_by(first_name=first_name).first()


def test_children_list_shows_registered_child(logged_in_client):
    _register_test_child(logged_in_client)
    response = logged_in_client.get("/admin/children")
    assert response.status_code == 200
    assert b"Olle Olsson" in response.data


def test_edit_child_updates_fields_and_logs_event(logged_in_client):
    child = _register_test_child(logged_in_client)

    response = logged_in_client.post(
        f"/admin/children/{child.id}/edit",
        data={
            "first_name": "Olle",
            "last_name": "Olsson-Andersson",
            "group_class": "Grupp 3",
            "birth_year": "2017",
            "guardian_name": "Ove Olsson",
            "guardian_phone": "0709998877",
            "guardian_email": "ove@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    updated = db.session.get(Child, child.id)
    assert updated.last_name == "Olsson-Andersson"
    assert updated.group_class == "Grupp 3"
    assert LogEntry.query.filter_by(event_type="child_updated", child_id=child.id).first() is not None


def test_edit_child_requires_login(client):
    response = client.get("/admin/children/1/edit", follow_redirects=True)
    assert response.status_code == 200
    assert "Logga in".encode() in response.data


def test_delete_child_erases_personal_data(logged_in_client):
    child = _register_test_child(logged_in_client)

    response = logged_in_client.post(f"/admin/children/{child.id}/delete", follow_redirects=True)
    assert response.status_code == 200

    erased = db.session.get(Child, child.id)
    assert erased.active is False
    assert erased.first_name == "Raderad"
    assert erased.guardians == []
