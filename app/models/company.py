from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Company(Model):
    id = fields.UUIDField(pk=True, index=True)
    # user = fields.ForeignKeyField(
    #     'models.User', related_name='user_company', on_delete='CASCADE')
    organization_code = fields.CharField(
        max_length=128, null=False, unique=True)  # mys = MYS8A3B2C1D
    # img_url = fields.CharField(max_length=500, null=True)
    name = fields.CharField(max_length=128, null=True)
    email = fields.CharField(max_length=128, null=True)
    phone = fields.CharField(max_length=128, null=True)
    address = fields.CharField(max_length=128, null=True)
    postal_code = fields.CharField(max_length=128, null=True)
    website = fields.CharField(max_length=128, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "companies"
        ordering = ["created_at"]


company_pydantic = pydantic_model_creator(
    Company, name='Company', exclude=('created_at'))
