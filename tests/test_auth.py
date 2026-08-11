def test_login_requires_valid_credentials(client, staff_user):
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "wrong-password"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Fel användarnamn eller lösenord".encode() in response.data


def test_login_success_redirects_to_dashboard(client, staff_user):
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "supersecret123"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Översikt".encode() in response.data


def test_admin_requires_login(client):
    response = client.get("/admin/", follow_redirects=True)
    assert response.status_code == 200
    assert "Logga in".encode() in response.data
