from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_Qualification_Licenses(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='employee_qualifications_licenses', on_delete='CASCADE')
    qualifications_licenses = fields.TextField(null=False)  # object
    prev_technical_work = fields.TextField(null=False)  # object
    # date
    # residence_status
    # institution_name
    # supervisor
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "employee_qualifications_licenses"
        ordering = ["created_at"]


emp_qualifications_licenses_pydantic = pydantic_model_creator(
    Emp_Qualification_Licenses, name="Emp_Qualification_Licenses", exclude=("created_at", ))
