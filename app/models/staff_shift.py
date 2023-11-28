from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Staff_Shift(Model):
    id = fields.UUIDField(pk=True, index=True)
    # staff = fields.ForeignKeyField(
    #     'models.Staff', related_name='sws', on_delete='CASCADE')
    staff = fields.CharField(max_length=128, null=True)
    patient = fields.CharField(max_length=128, null=True)
    service_type = fields.CharField(max_length=128, null=True)
    service_details = fields.TextField(null=True)
    start = fields.DatetimeField(null=True) # date valueof type
    end = fields.DatetimeField(null=True)# date valueof type
    duration = fields.CharField(max_length=5 ,null=False)
    remarks = fields.TextField(null=True)
    color = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "staff_shift"
        ordering = ["created_at"]


staff_shift_pydantic = pydantic_model_creator(
    Staff_Shift, name='Staff_Shift', exclude=('created_at'))
