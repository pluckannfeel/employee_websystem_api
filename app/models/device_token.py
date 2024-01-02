from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Device_Token(Model):
    id = fields.UUIDField(pk=True, index=True)
    token = fields.CharField(max_length=500, null=True)
    staff_code = fields.CharField(max_length=128, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "device_token"
        ordering = ["created_at"]


device_token_pydantic = pydantic_model_creator(
    Device_Token, name="Device_Token")
