from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Report(Model):
    id = fields.UUIDField(pk=True, index=True)
    shift = fields.ForeignKeyField(
        'models.Staff_Shift', related_name='staff_shift_report', on_delete='CASCADE')
    patient = fields.CharField(max_length=128, null=True)
    service_hours = fields.CharField(max_length=128, null=True)
    toilet_assistance = fields.TextField(null=True)
    meal_assistance = fields.TextField(null=True)
    bath_assistance = fields.TextField(null=True)
    grooming_assistance = fields.TextField(null=True)
    positioning_assistance = fields.TextField(null=True)
    medication_medical_care = fields.TextField(null=True)
    daily_assistance = fields.TextField(null=True)
    outgoing_assistance = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "shift_report"
        ordering = ["created_at"]


report_pydantic = pydantic_model_creator(
    Report, name='ShiftReport', exclude=('created_at'))
