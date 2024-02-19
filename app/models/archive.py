from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Archive(Model):
    id = fields.UUIDField(pk=True, index=True)
    key = fields.TextField(null=False, unique=True)
    name = fields.TextField(null=True)
    size = fields.IntField(null=True)
    last_modified = fields.DatetimeField(null=True)
    last_modified_by = fields.CharField(max_length=128, null=True)
