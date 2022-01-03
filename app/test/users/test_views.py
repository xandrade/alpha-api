import datetime as dt

import pytest
from tortoise.contrib import test


from app.user.models import Users, Friends, Videos, WatchedVideos, RefUrls


@pytest.mark.asyncio
async def test_app(client):

    response = await client.get("/auth")
    assert response.status_code == 401

    response = await client.get("/auth/")
    assert response.status_code == 401

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
        "message": "Thank you for sign-in!",
    }

    response = await client.post(
        "/auth/logon",
        json={"email": "test@test.com", "password": "password"},
    )
    assert response.status_code == 200
    assert (await response.get_json()) == {"message": "Logged in successfully"}

    response = await client.get("/auth/a")
    assert response.status_code == 200

    response = await client.get("/auth/home")
    assert response.status_code == 200

    response = await client.get("/auth/")
    assert response.status_code == 200

    response = await client.get("/auth/logout")
    assert response.status_code == 302  # redirected to login


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
