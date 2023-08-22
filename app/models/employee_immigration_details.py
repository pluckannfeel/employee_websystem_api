from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Emp_Immigration_Details(Model):
    id = fields.UUIDField(pk=True, index=True)
    employee = fields.ForeignKeyField(
        'models.Employee', related_name='emp_immigration_details', on_delete='CASCADE')
    passport_number = fields.CharField(max_length=128, null=True)
    passport_expiration_date = fields.DateField(null=True)
    old_passport_number_list = fields.CharField(
        max_length=256, null=True)  # object
    
    scheduled_departure_date = fields.DateField(null=True)
    scheduled_entry_date = fields.DateField(null=True)
    port_of_landing = fields.CharField(max_length=128, null=True)
    length_of_stay = fields.CharField(max_length=28, null=True)
    
    accompany = fields.CharField(max_length=10, null=True)
    place_of_visa_inspection = fields.CharField(max_length=128, null=True)
    
    actual_entry_date = fields.DateField(null=True)
    past_entry_count = fields.IntField(null=True)
    recent_entry_date = fields.DateField(null=True)
    recent_departure_date = fields.DateField(null=True)
    
    commited_offense = fields.CharField(max_length=10, null=True)
    commited_offense_details = fields.TextField(null=True)

    
    forced_departure = fields.CharField(max_length=10, null=True)
    forced_departure_count = fields.IntField(null=True)
    forced_departure_date_from = fields.DateField(null=True)
    forced_departure_date_to = fields.DateField(null=True)
    
    birth_place = fields.CharField(max_length=128, null=True)
    home_address = fields.CharField(max_length=256, null=True)
    
    present_address = fields.CharField(max_length=256, null=True)
    present_address_postal_code = fields.CharField(max_length=128, null=True)
    
    residence_card_number = fields.CharField(max_length=128, null=True)
    receipt_document_number = fields.CharField(max_length=128, null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "emp_immigration_details"
        ordering = ["created_at"]


emp_immigration_details_pydantic = pydantic_model_creator(
    Emp_Immigration_Details, name="Emp_Immigration_Details", exclude=("created_at", ))
