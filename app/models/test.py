from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Test(Model):
    id = fields.UUIDField(pk=True, index=True)