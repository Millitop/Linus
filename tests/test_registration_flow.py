from app.models import Card, LogEntry, Member


def test_self_registration_via_join_creates_member_and_card_no_login_required(client):
    response = client.post(
        "/join",
        data={"first_name": "Elsa", "last_name": "Eriksson", "phone": "0701234567"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    member = Member.query.filter_by(first_name="Elsa", last_name="Eriksson").first()
    assert member is not None
    assert member.active_card() is not None

    log = LogEntry.query.filter_by(event_type="registration", member_id=member.id).first()
    assert log is not None
    assert log.source == "web-app"
    assert log.staff_user_id is None


def test_self_registration_requires_name(client):
    response = client.post("/join", data={"first_name": "", "last_name": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert Member.query.count() == 0


def test_staff_assisted_registration_logs_admin_source(logged_in_client, staff_user):
    response = logged_in_client.post(
        "/admin/register",
        data={"first_name": "Filip", "last_name": "Falk", "phone": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200

    member = Member.query.filter_by(first_name="Filip").first()
    assert member is not None

    log = LogEntry.query.filter_by(event_type="registration", member_id=member.id).first()
    assert log.source == "admin"
    assert log.staff_user_id == staff_user.id


def test_reissue_card_revokes_old_and_creates_new(logged_in_client):
    logged_in_client.post(
        "/admin/register",
        data={"first_name": "Gustav", "last_name": "Gren"},
        follow_redirects=True,
    )
    member = Member.query.filter_by(first_name="Gustav").first()
    old_token = member.active_card().token

    logged_in_client.post(f"/admin/members/{member.id}/reissue-card", follow_redirects=True)

    old_card = Card.query.filter_by(token=old_token).first()
    assert old_card.active is False
    assert member.active_card().token != old_token
