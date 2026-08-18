def test_poster_requires_login(client):
    response = client.get("/admin/poster", follow_redirects=True)
    assert response.status_code == 200
    assert "Logga in".encode() in response.data


def test_poster_shows_join_and_tap_qr_codes(logged_in_client):
    response = logged_in_client.get("/admin/poster")
    assert response.status_code == 200
    assert b"/join" in response.data
    assert b"/gate/tap" in response.data
    # two embedded PNG QR codes, one per URL
    assert response.data.count(b"data:image/png;base64,") == 2
