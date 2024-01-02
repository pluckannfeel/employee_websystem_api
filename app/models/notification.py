from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Notification(Model):
    id = fields.UUIDField(pk=True, index=True)
    recipient = fields.CharField(max_length=128, null=True) # staff_code or user id
    code = fields.CharField(max_length=128, null=True)
    params = fields.JSONField(null=True)
    unread = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notification"
        ordering = ["created_at"]


notification_pydantic = pydantic_model_creator(
    Notification, name='Notification')
