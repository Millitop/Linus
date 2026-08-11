from app.models import Card, Child, LogEntry


def test_register_child_creates_card_and_logs_registration(logged_in_client):
    response = logged_in_client.post(
        "/admin/register",
        data={
            "first_name": "Elsa",
            "last_name": "Eriksson",
            "group_class": "Grupp 1",
            "birth_year": "2016",
            "guardian_name": "Erik Eriksson",
            "guardian_phone": "0701234567",
            "guardian_email": "erik@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    child = Child.query.filter_by(first_name="Elsa", last_name="Eriksson").first()
    assert child is not None
    assert child.active_card() is not None
    assert len(child.guardians) == 1

    log = LogEntry.query.filter_by(event_type="registration", child_id=child.id).first()
    assert log is not None


def test_reissue_card_revokes_old_and_creates_new(logged_in_client):
    logged_in_client.post(
        "/admin/register",
        data={
            "first_name": "Filip",
            "last_name": "Falk",
            "guardian_name": "Fia Falk",
        },
        follow_redirects=True,
    )
    child = Child.query.filter_by(first_name="Filip").first()
    old_token = child.active_card().token

    logged_in_client.post(f"/admin/children/{child.id}/reissue-card", follow_redirects=True)

    old_card = Card.query.filter_by(token=old_token).first()
    assert old_card.active is False
    assert child.active_card().token != old_token
