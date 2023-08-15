from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_Relatives(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='emp_relatives', on_delete='CASCADE')
    relatives = fields.TextField(null=False)  # object
    # id
    # relationship
    # name
    # birthdate
    # nationality
    # to_petition (yes or no)
    # workplace_or_school
    # residence_card_number
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "emp_relatives"
        ordering = ["created_at"]


emp_relatives_pydantic = pydantic_model_creator(
    Emp_Relatives, name="Emp_Relatives", exclude=("created_at", ))
