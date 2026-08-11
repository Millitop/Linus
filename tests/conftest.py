import pytest

from app import create_app
from app.extensions import db
from app.models import StaffUser


@pytest.fixture
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def staff_user(app):
    user = StaffUser(username="admin", display_name="Admin", role="admin")
    user.set_password("supersecret123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client, staff_user):
    payload = {"username": "admin", "password": "supersecret123"}
    client.post("/auth/login", data=payload, follow_redirects=True)
    return client
