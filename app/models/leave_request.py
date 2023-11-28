from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Leave_Request(Model):
    id = fields.UUIDField(pk=True, index=True)
    staff = fields.ForeignKeyField(
        'models.Staff', related_name='staff_leave_request', on_delete='CASCADE')
    leave_type = fields.CharField(max_length=128, null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    details = fields.TextField(null=True)
    status = fields.CharField(max_length=128, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "leave_request"
        ordering = ["created_at"]


leave_request_pydantic = pydantic_model_creator(
    Leave_Request, name='LeaveRequest', exclude=('created_at'))
