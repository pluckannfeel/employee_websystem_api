from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic.creator import pydantic_model_creator


class Employee(Model):
    id = fields.UUIDField(pk=True, index=True)
    user = fields.ForeignKeyField(
        'models.User', related_name='user_employees', on_delete='CASCADE')
    name_romaji = fields.CharField(max_length=256, null=False)
    name_kanji = fields.CharField(max_length=128, null=True)
    name_kana = fields.CharField(max_length=256, null=False)
    img_url = fields.CharField(max_length=500, null=True)
    nationality = fields.CharField(max_length=128, null=True)
    gender = fields.CharField(max_length=5, null=True)
    age = fields.IntField(null=True)
    birth_date = fields.DateField(null=True)
    
    email = fields.CharField(max_length=128, null=True, unique=False)
    contact_number = fields.CharField(max_length=128, null=True)
    has_spouse = fields.CharField(max_length=5, null=True)
    primary_language = fields.CharField(max_length=128, null=True)
    start_date = fields.DateField(null=True)
    role = fields.CharField(max_length=128, null=True)
    # place of business in case of direct employment
    work_area_section = fields.CharField(max_length=128, null=True)
    company_name = fields.CharField(max_length=128, null=True)
    company_address = fields.CharField(max_length=128, null=True)
    company_postal_code = fields.CharField(max_length=64, null=True)
    work_conditions_master = fields.CharField(max_length=128, null=True)
    work_conditions_japanese = fields.CharField(max_length=128, null=True)
    reg_support_manager = fields.CharField(max_length=128, null=True)
    reg_support_staff = fields.CharField(max_length=128, null=True)
    affiliated_support_manager = fields.CharField(max_length=128, null=True)
    affiliated_support_staff = fields.CharField(max_length=128, null=True)
    intermediary_name= fields.CharField(max_length=128, null=True)
    intermediary_address= fields.CharField(max_length=256, null=True)
    intermediary_agency_name= fields.CharField(max_length=128, null=True)
    intermediary_contact_number= fields.CharField(max_length=128, null=True)
    enrollment_status = fields.CharField(max_length=128, null=False)
    return_date = fields.DateField(null=True)
    specified_skills_object = fields.CharField(max_length=512, null=True) # object
    # [{
        # id : 1,
        # specified_skills_period_from : 2020-01-01,
        # specified_skills_period_to : 2020-01-01,     
        # },
        # {
        # id : 2,
        # specified_skills_period_from : 2020-01-01,
        # specified_skills_period_to : 2020-01-01,
        # }
    # ]
    foreigner_skills_category = fields.CharField(max_length=128, null=False)
    foreigner_skills_category_status = fields.BooleanField(default=False, null=True)
    status_of_residence = fields.CharField(max_length=128, null=True)
    memo = fields.TextField(null=True)
    # display_order = fields.IntField(null=False) # included but not needed
    created_at = fields.DatetimeField(auto_now_add=True)
    disabled = fields.BooleanField(null=False, default=False)
    # @staticmethod
    # def get_full_name(self) -> str:
    #     return self.name_romaji

    def __str__(self):
        return self.name_romaji

    class Meta:
        table = "employees"
        ordering = ["created_at"]
        
employee_pydantic = pydantic_model_creator(
    Employee, name="Employee", exclude=("created_at", )
)
employeeIn_pydantic = pydantic_model_creator(
    Employee, name="EmployeeIn", exclude_readonly=True, exclude=("created_at",)
)

employeeOut_pydantic = pydantic_model_creator(
    Employee, name="EmployeeOut",
)

