def test_dashboard_default_period_is_30_days(logged_in_client):
    response = logged_in_client.get("/admin/")
    assert response.status_code == 200
    assert b"30 dagar" in response.data


def test_dashboard_accepts_valid_period(logged_in_client):
    response = logged_in_client.get("/admin/?period=7")
    assert response.status_code == 200
    assert b"senaste 7 dagarna" in response.data


def test_dashboard_falls_back_to_default_on_invalid_period(logged_in_client):
    response = logged_in_client.get("/admin/?period=999")
    assert response.status_code == 200
    assert b"senaste 30 dagarna" in response.data


def test_stats_export_csv_has_header_and_rows(logged_in_client):
    response = logged_in_client.get("/admin/stats/export.csv?period=7")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    body = response.data.decode("utf-8")
    lines = body.strip().splitlines()
    assert lines[0] == "date,besök"
    assert len(lines) == 8  # header + 7 days


def test_stats_export_requires_login(client):
    response = client.get("/admin/stats/export.csv", follow_redirects=True)
    assert response.status_code == 200
    assert "Logga in".encode() in response.data
