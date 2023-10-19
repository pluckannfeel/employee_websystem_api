from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class MedicalInstitution(Model):
    id = fields.UUIDField(pk=True, index=True)
    physician_name_kanji = fields.CharField(max_length=128, null=True)
    physician_name_kana = fields.CharField(max_length=128, null=True)
    physician_birth_date = fields.DateField(null=True)
    physician_age = fields.CharField(max_length=10, null=True)
    physician_work = fields.CharField(max_length=128, null=True)
    entity_name = fields.CharField(max_length=128, null=True)
    entity_poc = fields.CharField(max_length=128, null=True)
    medical_institution_name = fields.CharField(max_length=128, null=True)
    medical_institution_poc = fields.CharField(max_length=128, null=True)
    medical_institution_postal_code = fields.CharField(
        max_length=128, null=True)
    medical_institution_address1 = fields.CharField(max_length=256, null=True)
    medical_institution_address2 = fields.CharField(max_length=256, null=True)
    medical_institution_phone = fields.CharField(max_length=128, null=True)
    medical_institution_fax = fields.CharField(max_length=128, null=True)
    medical_institution_email = fields.CharField(max_length=128, null=True)
    medical_institution_type = fields.CharField(max_length=128, null=True)
    licenses = fields.TextField(null=True)  # list or tuple
    license_number = fields.CharField(max_length=128, null=True)
    date_obtained = fields.DateField(null=True)
    ojt_implementation_name = fields.CharField(max_length=128, null=True)
    data_disabled = fields.BooleanField(null=False, default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "medical_institutions"
        ordering = ["created_at"]


medical_institution_pydantic = pydantic_model_creator(
    MedicalInstitution, name='MedicalInstitution', exclude=('created_at'))
