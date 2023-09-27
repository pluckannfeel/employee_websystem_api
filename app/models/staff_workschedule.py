from tortoise.models import Model
from tortoise import fields
from tortoise.contrb.pydantic.creator import pydantic_model_creator

class StaffWorkSchedule(Model):
    id = fields.UUIDField(pk=True, index=True)