from typing import Optional
import json

from tortoise.models import Model
from tortoise import fields
from quart_auth import AuthUser


class Friends(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=320)
    given_name = fields.CharField(max_length=50, default=None)
    archived = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Users_(AuthUser):
    def __init__(self, auth_id):
        super().__init__(auth_id)
        self._resolved = False
        self._email = None

    async def _resolve(self):
        if not self._resolved:
            user = await Users.filter(auth_id=self.auth_id).first()
            self._email = user.email
            self._resolved = True

    @property
    async def email(self):
        await self._resolve()
        return self._email


class Users(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=320, unique=True)
    password = fields.CharField(max_length=117)
    given_name = fields.CharField(max_length=50, null=True)
    credits = fields.IntField(default=100)
    email_validation_code = fields.TextField(default="")
    email_validated = fields.BooleanField(default=False)
    profile_completed = fields.BooleanField(default=False)
    newsletter_subcribed = fields.BooleanField(default=True)
    max_clients = fields.IntField(default=2)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class YTClients(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Videos(Model):
    id = fields.IntField(pk=True)
    user_id = fields.ForeignKeyField(
        "models.Users", related_name="videos", on_delete=fields.CASCADE
    )
    video_url = fields.TextField()
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
