from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_RES_History(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='emp_res_history', on_delete='CASCADE')
    relatives = fields.TextField(null=False)  # object
    employment_history = fields.TextField(null=False)  # object
    # start_date
    # end_date
    # company_name
    school_history = fields.TextField(null=False)  # object
    # start_date
    # end_date
    # school_name
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "employee_res_history"
        ordering = ["created_at"]


emp_res_pydantic = pydantic_model_creator(
    Emp_RES_History, name="Emp_RES_History", exclude=("created_at", ))
