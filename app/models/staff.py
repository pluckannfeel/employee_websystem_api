from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Staff(Model):
    id = fields.UUIDField(pk=True, index=True)
    user = fields.ForeignKeyField('models.User', related_name='user_staff', on_delete='CASCADE')
    img_url = fields.CharField(max_length=500, null=True)
    affiliation = fields.CharField(max_length=128, null=True) #所属
    staff_group = fields.CharField(max_length=128, null=True) #ユーザーグループ 介護ヘルパー and 利用者
    staff_code = fields.CharField(max_length=64, null=True)
    # added on sep 6
    japanese_name = fields.CharField(max_length=128, null=True)
    english_name = fields.CharField(max_length=128, null=True)
    nationality = fields.CharField(max_length=128, null=True)
    gender = fields.CharField(max_length=128, null=True)
    job_position = fields.CharField(max_length=128, null=True) 
    duty_type = fields.CharField(max_length=128, null=True) #勤務形態
    # added on sep 6
    birth_date = fields.DateField(null=True)
    join_date = fields.DateField(null=True)
    leave_date = fields.DateField(null=True)
    postal_code = fields.CharField(max_length=20, null=True)
    prefecture = fields.CharField(max_length=128, null=True)
    municipality = fields.CharField(max_length=128, null=True)
    town = fields.CharField(max_length=128, null=True)
    building = fields.CharField(max_length=128, null=True)
    phone_number = fields.CharField(max_length=128, null=True) #職員電話番号
    email = fields.CharField(max_length=128, null=True)
    koyou_keitai = fields.CharField(max_length=128, null=True) #雇用形態 Employment status
    zaishoku_joukyou = fields.CharField(max_length=128, null=True) #在職状況 Employment status
    licenses = fields.TextField(null=True) 
    # license_number 
    # license_name
    # license_date
    # license_file_link

    # nursing_care_specialist = fields.CharField(max_length=128, null=True) #介護支援専門員
    # certified_care_worker = fields.CharField(max_length=128, null=True) #介護福祉士
    # home_helper_level1 = fields.CharField(max_length=128, null=True) #ホームヘルパー1級
    # home_helper_level2 = fields.CharField(max_length=128, null=True) #ホームヘルパー2級
    # beginner_care_workers_training = fields.CharField(max_length=128, null=True) #介護職員初任者研修
    # practical_care_workers_training = fields.CharField(max_length=128, null=True) #介護福祉士実務者研修
    # basic_pwd_care_workers_training = fields.CharField(max_length=128, null=True) #障害者居宅介護従業者基礎研修課程 Basic training course for in-home care workers for persons with disabilities
    # basic_shv_care_employees_training = fields.CharField(max_length=128, null=True) #重度訪問介護従業者養成研修(基礎) Training for Employees of Severe Home-Visit Care (Basic)
    # basic_shv_care_employees_training_plus = fields.CharField(max_length=128, null=True) #重度訪問介護従業者養成研修(追加) Training for Employees of Severe Home-Visit Care (additional)
    disabled = fields.BooleanField(null=False, default=False) # instead of deleting the record, we just set this to true
    created_at = fields.DatetimeField(auto_now_add=True)
    
staff_pydantic = pydantic_model_creator(Staff, name='Staff', exclude=('created_at'))
# staff_pydantic_in = pydantic_model_creator(Staff, name='StaffIn', exclude_readonly=True)
# staff_pydantic_out = pydantic_model_creator(Staff, name='StaffOut', exclude=('created_at', 'user_id', 'disabled'))