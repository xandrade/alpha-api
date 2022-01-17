from typing import Optional
import json
from quart.ctx import AppContext

from tortoise.models import Model
from tortoise import fields
from quart_auth import AuthUser

from app.extensions import bcrypt


class Friends(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=320)
    given_name = fields.CharField(max_length=50, default=None)
    archived = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Users(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=80, unique=True, null=False)
    email = fields.CharField(max_length=320, unique=True, null=False)
    _password = fields.BinaryField("password", max_length=128, null=True)
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)
    credits = fields.IntField(default=100)
    email_validation_code = fields.TextField(default="")
    email_validated = fields.BooleanField(default=False)
    profile_completed = fields.BooleanField(default=False)
    newsletter_subcribed = fields.BooleanField(default=True)
    max_clients = fields.IntField(default=2)
    active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    @property
    def password(self):
        """Hashed password."""
        return self._password

    @password.setter
    def password(self, value):
        """Set password."""
        from passlib.context import CryptContext

        self._password = bcrypt.generate_password_hash(value)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self._password, value)

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Users({self.username!r})>"


class YTClients(Model):
    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        "models.Users", related_name="ytclients", on_delete=fields.CASCADE
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Videos(Model):
    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        "models.Users", related_name="videos", on_delete=fields.CASCADE
    )
    video_id = fields.TextField()
    video_url = fields.TextField()
    video_title = fields.TextField()
    duration = fields.IntField()
    archived = fields.BooleanField(default=False)
    views_enabled = fields.BooleanField(default=True)
    credits_per_view = fields.IntField(default=3, max=30)
    created_at = fields.DatetimeField(auto_now_add=True)


class WatchedVideos(Model):
    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        "models.Users", related_name="watched_videos", on_delete=fields.CASCADE
    )
    video_id = fields.ForeignKeyField(
        "models.Videos", related_name="watched_videos", on_delete=fields.CASCADE
    )
    ref_id = fields.ForeignKeyField(
        "models.RefUrls", related_name="watched_videos", on_delete=fields.CASCADE
    )
    created_at = fields.DatetimeField(auto_now_add=True)


class RefUrls(Model):
    id = fields.IntField(pk=True)
    ref_url = fields.TextField()
    enable = fields.BooleanField(default=True)
    archived = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)


class Navigation(Model):
    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        "models.Users", related_name="navigation", on_delete=fields.CASCADE
    )
    session_id = fields.TextField()
    url = fields.TextField()
    ip_address = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)


class User(AuthUser):
    def __init__(self, auth_id):
        super().__init__(auth_id)
        self._resolved = False
        self._email = None
        self._is_admin = None
        self._username = None
        self._full_name = None

    async def _resolve(self):
        if not self._resolved:
            user = await Users.filter(id=self.auth_id).first()
            self._email = user.email
            self._is_admin = user.is_admin
            self._username = user.username
            self._full_name = user.fullname
            self._resolved = True

    @property
    async def email(self):
        await self._resolve()
        return self._email

    @property
    async def is_admin(self):
        await self._resolve()
        return self._is_admin

    @property
    async def given_name(self):
        await self._resolve()
        return self._given_name
