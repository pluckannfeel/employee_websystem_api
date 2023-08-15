from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_Qualification(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='emp_qualifications', on_delete='CASCADE')
    qualifications = fields.TextField(null=False)  # object
    prev_technical_training = fields.TextField(null=False)  # object
    # date
    # residence_status
    # institution_name
    # supervisor
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "emp_qualifications"
        ordering = ["created_at"]


emp_qualifications_pydantic = pydantic_model_creator(
    Emp_Qualification, name="Emp_Qualification", exclude=("created_at", ))
