from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Staff_Payslip(Model):
    id = fields.UUIDField(pk=True, index=True)
    staff = fields.ForeignKeyField(
        'models.Staff', related_name='staff_payslip', on_delete='CASCADE')
    release_date = fields.DateField(null=True)
    file_url = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    net_salary = fields.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    total_deduction = fields.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    total_hours = fields.DecimalField(
        max_digits=10, decimal_places=2, null=True)

    class Meta:
        table = 'staff_payslip'


staff_payslip_pydantic = pydantic_model_creator(
    Staff_Payslip, name='Staff_Payslip')
