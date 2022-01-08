import datetime as dt

import pytest
from tortoise.contrib import test


from app.user.models import Users, Friends, Videos, WatchedVideos, RefUrls


@pytest.mark.asyncio
async def test_app(client):

    # Check rederected from the auth blueprint
    response = await client.get("/auth")
    assert response.status_code == 308

    # Follow redirect and check if can access
    response = await client.get("/auth", follow_redirects=True)
    assert response.status_code == 401

    # Check if can access
    response = await client.get("/auth/")
    assert response.status_code == 401

    # Create user
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 200  # redirected to login
    assert (await response.get_json()) == {
        "status": "success",
        "message": "Thank you for sign-in!.",
    }

    # Create duplicate user
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "User already exists.",
    }

    # Create user with missing email
    response = await client.post(
        "/auth/signup",
        json={
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing data.",
    }

    # Create user with missing password
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing data.",
    }

    # Create user with missing username
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "password": "password",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing data.",
    }

    # Create user with missing first name
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "password": "password",
            "username": "username",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing data.",
    }

    # Create user with missing last name
    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test.com",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing data.",
    }

    response = await client.post(
        "/auth/signup",
        json={
            "email": "test.com",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    r = await response.get_json()
    assert r["status"] == "unsuccess"

    response = await client.post(
        "/auth/signup",
        json={
            "email": "test@test..com",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    r = await response.get_json()
    assert r["status"] == "unsuccess"

    response = await client.post(
        "/auth/signup",
        json={
            "email": "чебурашкаящик-с-апельсинами.рф@example.tld'",
            "password": "password",
            "username": "username",
            "first_name": "firt name",
            "last_name": "last name",
        },
    )
    assert response.status_code == 400
    r = await response.get_json()
    assert r["status"] == "unsuccess"

    # Check loging with user
    response = await client.post(
        "/auth/logon",
        json={"email": "test@test.com", "password": "password"},
    )
    assert response.status_code == 200
    assert (await response.get_json()) == {
        "status": "success",
        "message": "Logged in successfully.",
    }

    # check if can access some routes
    routes = [
        "/auth/home",
        "/auth/a",
        "/auth/",
    ]
    for route in routes:
        response = await client.get(route)
        assert response.status_code == 200

    # Test loging out
    response = await client.get("/auth/logout")
    assert response.status_code == 302  # redirected to login

    # Check if can access restricted routes after logged out
    for route in routes:
        response = await client.get(route)
        assert response.status_code == 401

    # Check loging with wrong or unexisted user
    response = await client.post(
        "/auth/logon",
        json={"email": "wrong@test.com", "password": "password"},
    )
    assert response.status_code == 404
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "User is not registered.",
    }

    # Check loging with wrong password
    response = await client.post(
        "/auth/logon",
        json={"email": "test@test.com", "password": "unlocked"},
    )
    assert response.status_code == 403
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
    }

    # Check loging with no email
    response = await client.post(
        "/auth/logon",
        json={"password": "password"},
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing email or password.",
    }

    # Check loging with no password
    response = await client.post(
        "/auth/logon",
        json={
            "email": "test@test.com",
        },
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "Missing email or password.",
    }

    # Check loging with no data (json)
    response = await client.post(
        "/auth/logon",
    )
    assert response.status_code == 400
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
    }

    await Users.filter(email="test@test.com").update(active=False)

    # Check loging with inactive user
    response = await client.post(
        "/auth/logon",
        json={"email": "test@test.com", "password": "password"},
    )
    assert response.status_code == 403
    assert (await response.get_json()) == {
        "status": "unsuccess",
        "message": "User is not active.",
    }


class TestUsers(test.TestCase):
    """Users tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = Users(username="foo", email="foo@bar.com")
        user.create()

        retrieved = Users.get_by_id(user.id)
        assert retrieved == user

    def test_created_at_defaults_to_datetime(self):
        """Test creation date."""
        user = Users(username="foo", email="foo@bar.com")
        user.save()
        assert bool(user.created_at)
        assert isinstance(user.created_at, dt.datetime)

    def test_password_is_nullable(self):
        """Test null password."""
        user = Users(username="foo", email="foo@bar.com")
        user.save()
        assert user.password is None

    def test_factory(self, db):
        """Test user factory."""
        user = UserFactory(password="myprecious")
        db.session.commit()
        assert bool(user.username)
        assert bool(user.email)
        assert bool(user.created_at)
        assert user.is_admin is False
        assert user.active is True
        assert user.check_password("myprecious")

    def test_check_password(self):
        """Check password."""
        user = User.create(username="foo", email="foo@bar.com", password="foobarbaz123")
        assert user.check_password("foobarbaz123") is True
        assert user.check_password("barfoobaz") is False

    def test_full_name(self):
        """User full name."""
        user = UserFactory(first_name="Foo", last_name="Bar")
        assert user.full_name == "Foo Bar"

    def test_roles(self):
        """Add a role to a user."""
        role = Role(name="admin")
        role.save()
        user = UserFactory()
        user.roles.append(role)
        user.save()
        assert role in user.roles

    def test_roles_repr(self):
        """Check __repr__ output for Role."""
        role = Role(name="user")
        assert role.__repr__() == "<Role(user)>"

    def test_user_repr(self):
        """Check __repr__ output for User."""
        user = User(username="foo", email="foo@bar.com")
        assert user.__repr__() == "<User('foo')>"
