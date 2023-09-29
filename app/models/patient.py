from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator

class Patient(Model):
    id = fields.UUIDField(pk=True, index=True)
    user = fields.ForeignKeyField('models.User', related_name='user_patient', on_delete='CASCADE')
    affiliation = fields.CharField(max_length=128, null=True) #所属
    name_kanji = fields.CharField(max_length=128, null=True)
    name_kana = fields.CharField(max_length=128, null=True)
    birth_date = fields.DateField(null=True)
    gender = fields.CharField(max_length=64, null=True)
    postal_code = fields.CharField(max_length=20, null=True)
    prefecture = fields.CharField(max_length=128, null=True)
    municipality = fields.CharField(max_length=128, null=True)
    town = fields.CharField(max_length=128, null=True)
    building = fields.CharField(max_length=128, null=True)
    telephone_number = fields.CharField(max_length=128, null=True)
    phone_number = fields.CharField(max_length=128, null=True)
    billing_method = fields.CharField(max_length=128, null=True) #請求方法
    billing_address = fields.CharField(max_length=128, null=True) #請求先
    billing_postal_code = fields.CharField(max_length=20, null=True) #請求先郵便番号
    patient_status = fields.CharField(max_length=128, null=True) #利用者状況
    remarks = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "patients"
        ordering = ["created_at"]
    
patient_pydantic = pydantic_model_creator(Patient, name='Patient', exclude=('created_at'))