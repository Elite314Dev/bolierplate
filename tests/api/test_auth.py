import pytest

from itsdangerous import JSONWebSignatureSerializer
from requests import codes

from boilerplateapp.extensions import db
from boilerplateapp.models.user import User


@pytest.mark.usefixtures('dbmodels', 'dbtransaction')
class TestLogin:
    def test_success(self, app, client, user):
        """Clients can log in and get back a valid JWT token."""
        resp = client.post("/login", data={"email": user.email, "password": "test"})
        assert resp.status_code == codes.OK
        assert resp.json['data']

        serializer = JSONWebSignatureSerializer(app.config['SECRET_KEY'], salt='login')
        assert serializer.loads(resp.json['data'])['id'] == user.id

    def test_fail_wrong_username(self, app, client, user):
        """Clients can't login with a wrong username and get an error."""
        resp = client.post("/login", data={"email": "invalid@example.com", "password": "test"})
        assert resp.status_code == codes.UNAUTHORIZED
        assert not resp.json.get('data')

    def test_fail_wrong_password(self, app, client, user):
        """Clients can't login with a wrong username and get an error."""
        resp = client.post("/login", data={"email": user.email, "password": "invalid"})
        assert resp.status_code == codes.UNAUTHORIZED
        assert not resp.json.get('data')


@pytest.mark.usefixtures('dbmodels', 'dbtransaction')
class TestRegister:
    def test_success(self, app, client):
        """Clients can register a new account with email and password and then log in with it."""
        new_email = "newuser@example.com"
        new_password = "test"
        resp = client.post("/register", data={"email": new_email, "password": new_password})
        assert resp.status_code == codes.CREATED
        new_user_id = resp.json['data']['id']
        assert resp.json['data'] == {"id": new_user_id, "email": new_email}

        # Now try to log in using the new account.
        resp = client.post("/login", data={"email": new_email, "password": new_password})
        assert resp.status_code == codes.OK
        assert resp.json['data']

        serializer = JSONWebSignatureSerializer(app.config['SECRET_KEY'], salt='login')
        assert serializer.loads(resp.json['data'])['id'] == new_user_id

    def test_fail_on_duplicate_email(self, app, client):
        """Clients can't register with an existing email."""
        new_email = "newuser@example.com"
        new_password = "test"
        resp = client.post("/register", data={"email": new_email, "password": new_password})
        assert resp.status_code == codes.CREATED

        # Now try to create a new account with the same email.
        resp = client.post("/register", data={"email": new_email, "password": new_password})
        assert resp.status_code == codes.CONFLICT

    def test_fail_on_invalid(self, app, client):
        """Clients can't register with an invalid email."""
        new_email = "invalid"
        new_password = "test"
        resp = client.post("/register", data={"email": new_email, "password": new_password})
        assert resp.status_code == codes.UNPROCESSABLE_ENTITY
        assert db.session.query(User).count() == 0
