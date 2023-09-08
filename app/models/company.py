from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator

class Company(Model):
    id = fields.UUIDField(pk=True, index=True)
    user = fields.ForeignKeyField('models.User', related_name='user_company', on_delete='CASCADE')
    img_url = fields.CharField(max_length=500, null=True)
    company_name = fields.CharField(max_length=128, null=True)