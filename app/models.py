from tortoise.models import Model
from tortoise import fields


class Friends(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    email = fields.TextField()
    subcribed = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return f"Friend {self.id}: {self.name}, {self.email}, {self.subcribed}, {self.created_at}, {self.updated_at}"
