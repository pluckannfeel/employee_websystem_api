from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Staff(Model):
    id = fields.UUIDField(pk=True, index=True)
    user = fields.ForeignKeyField(
        'models.User', related_name='user_staff', on_delete='CASCADE')
    img_url = fields.CharField(max_length=500, null=True)
    affiliation = fields.CharField(max_length=128, null=True)  # 所属
    staff_group = fields.CharField(
        max_length=128, null=True)  # ユーザーグループ 介護ヘルパー and 利用者
    staff_code = fields.CharField(max_length=64, null=True)
    # added on sep 6
    japanese_name = fields.CharField(max_length=128, null=True)
    english_name = fields.CharField(max_length=128, null=True)
    nickname = fields.CharField(max_length=128, null=True)
    nationality = fields.CharField(max_length=128, null=True)
    gender = fields.CharField(max_length=128, null=True)
    job_position = fields.CharField(max_length=128, null=True)
    duty_type = fields.CharField(max_length=128, null=True)  # 勤務形態
    # added on sep 6
    birth_date = fields.DateField(null=True)
    join_date = fields.DateField(null=True)
    leave_date = fields.DateField(null=True)
    postal_code = fields.CharField(max_length=20, null=True)
    prefecture = fields.CharField(max_length=128, null=True)
    municipality = fields.CharField(max_length=128, null=True)
    town = fields.CharField(max_length=128, null=True)
    building = fields.CharField(max_length=128, null=True)
    phone_number = fields.CharField(max_length=128, null=True)  # 職員電話番号
    personal_email = fields.CharField(max_length=128, null=True)
    work_email = fields.CharField(max_length=128, null=True)
    koyou_keitai = fields.CharField(
        max_length=128, null=True)  # 雇用形態 Employment status
    zaishoku_joukyou = fields.CharField(
        max_length=128, null=True)  # 在職状況 Employment status
    licenses = fields.TextField(null=True)
    # license_number
    # license_name
    # license_date
    # license_file_link
    # bank_details = fields.TextField(null=True)
    customer_number = fields.CharField(max_length=64, null=True)  # 顧客番号
    bank_name = fields.CharField(max_length=64, null=True)  # 銀行名
    branch_name = fields.CharField(max_length=64, null=True)  # 支店名
    account_type = fields.CharField(max_length=64, null=True)  # 口座種別
    account_number = fields.CharField(max_length=64, null=True)  # 口座番号
    account_name = fields.CharField(max_length=64, null=True)  # 口座名義
    bank_card_images = fields.TextField(null=True)  # 銀行カード画像
    passport_details = fields.TextField(null=True)  # パスポート詳細
    residence_card_details = fields.TextField(null=True)  # 在留カード画像
    # instead of deleting the record, we just set this to true
    disabled = fields.BooleanField(null=False, default=False)
    created_at = fields.DatetimeField(auto_now_add=True)


staff_pydantic = pydantic_model_creator(
    Staff, name='Staff', exclude=('created_at'))

# create a pydantic that only takes id, english_name, japanese_name, staff_group, duty_type
staffSelect_pydantic = pydantic_model_creator(Staff, name='StaffSelect', include=(
    'id', 'english_name', 'japanese_name', 'affiliation', 'prefecture', 'municipality', 'town', 'building', 'duty_type', 'birth_date', 'gender'))

# staff_pydantic_in = pydantic_model_creato˝r(Staff, name='StaffIn', exclude_readonly=True)
# staff_pydantic_out = pydantic_model_creator(Staff, name='StaffOut', exclude=('created_at', 'user_id', 'disabled'))
