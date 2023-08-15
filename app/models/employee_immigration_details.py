from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_Immigration_Details(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='emp_immigration_details', on_delete='CASCADE')
    passport_number = fields.CharField(max_length=128, null=False)
    residence_card_number = fields.CharField(max_length=128, null=False)
    receipt_number = fields.CharField(max_length=128, null=False)
    effective_date = fields.DateField(null=False)
    passport_number_list = fields.CharField(
        max_length=256, null=False)  # object
    departure_date = fields.DateField(null=False)
    entry_date = fields.DateField(null=False)
    port_of_landing = fields.CharField(max_length=128, null=False)
    length_of_stay = fields.IntField(null=False)
    accompany = fields.BooleanField(default=False, null=False)
    place_of_visa_application = fields.CharField(max_length=128, null=False)
    prev_entry_count = fields.IntField(null=False)
    prev_entry_date = fields.DateField(null=False)
    prev_departure_date = fields.DateField(null=False)
    commited_offense = fields.BooleanField(default=False, null=False)
    commited_offense_details = fields.TextField(null=False)
    forced_departure_count = fields.IntField(null=False)
    recent_forced_departure_date = fields.DateField(null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "emp_immigration_details"
        ordering = ["created_at"]


emp_immigration_details_pydantic = pydantic_model_creator(
    Emp_Immigration_Details, name="Emp_Immigration_Details", exclude=("created_at", ))
