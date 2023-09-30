from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Staff_WorkSchedule(Model):
    id = fields.UUIDField(pk=True, index=True)
    # staff_id
    staff = fields.ForeignKeyField('models.Staff', related_name='sws', on_delete='CASCADE') 
    description = fields.CharField(max_length=128, null=True)
    # timestamp
    start = fields.DatetimeField(null=False)
    end = fields.DatetimeField(null=False)
    color = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "staff_workschedules"
        ordering = ["created_at"]

staff_workschedule_pydantic = pydantic_model_creator(Staff_WorkSchedule, name='Staff_WorkSchedule', exclude=('created_at'))