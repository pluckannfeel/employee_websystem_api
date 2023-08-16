from datetime import date
from fastapi import UploadFile
from pydantic import BaseModel, EmailStr, SecretStr, root_validator
# import email_validator


class GetEmployeeDetails(BaseModel):
    employee: str

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        return values

# class ImageInfo(BaseModel):
#     file_name: str
#     content_type: str
#     image_data: bytes 

class CreateEmployee(BaseModel):
    user_id: str  # get the id of the user from the email
    # name_romaji: str
    # name_kanji: str
    # name_kana: str
    # nationality: str
    # gender: str
    # age: int
    # birth_date: date
    # birth_place: str
    # present_address: str
    # postal_code: str
    # home_address: str
    # email: EmailStr
    # contact_number: str
    # has_spouse: bool
    # primary_language: str
    # start_date: date
    # role: str
    # company_name: str
    # work_area_section: str
    # company_address: str
    # work_conditions_master: str
    # work_conditions_japanese: str
    # reg_support_manager: str
    # reg_support_staff: str
    # affiliated_support_manager: str
    # affiliated_support_staff: str
    # intermediary_name: str
    # intermediary_address: str
    # intermediary_agency_name: str
    # intermediary_contact_number: str
    # enrollment_status: str
    # return_date: date
    # specified_skills_object: str
    # foreigner_skills_category: str
    # foreigner_skills_category_status: bool
    # status_of_residence: str
    # memo: str
    # display_order: int

    # class Config:
    #     json_encoders = {
    #         SecretStr: lambda v: v.get_secret_value() if v else None
    #     }

    # @root_validator(pre=True)
    # def user_validator(cls, values):
    #     # check values if there is one null
    #     for value in values:
    #         if len(str(values.get(value))) == 0:
    #             raise ValueError(f'Form has an empty field. : {value}')

    #     return values


class UpdateEmployee(BaseModel):
    id: str
    name_romaji: str
    name_kanji: str
    name_kana: str
    nationality: str
    gender: str
    age: int
    birth_date: date
    birth_place: str
    present_address: str
    postal_code: str
    home_address: str
    email: EmailStr
    contact_number: str
    has_spouse: bool
    primary_language: str
    start_date: date
    role: str
    company_name: str
    work_area_section: str
    company_address: str
    work_conditions_master: str
    work_conditions_japanese: str
    reg_support_manager: str
    reg_support_staff: str
    affiliated_support_manager: str
    affiliated_support_staff: str
    intermediary_name: str
    intermediary_address: str
    intermediary_agency_name: str
    intermediary_contact_number: str
    enrollment_status: str
    return_date: date
    specified_skills_object: str
    foreigner_skills_category: str
    foreigner_skills_category_status: bool
    status_of_residence: str
    memo: str
    # display_order: int

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class DeleteEmployee(BaseModel):
    id: str
    user: str


class CreateEmployeeImmigrationDetails(BaseModel):
    employee: str
    passport_number: str
    residence_card_number: str
    receipt_number: str
    effective_date: date
    passport_number_list: str
    departure_date: date
    entry_date: date
    port_of_landing: str
    length_of_stay: int
    accompany: bool
    place_of_visa_application: str
    prev_entry_count: int
    prev_entry_date: date
    prev_departure_date: date
    commited_offense: bool
    commited_offense_details: str
    forced_departure_count: int
    recent_forced_departure_date: date

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class UpdateEmployeeImmigrationDetails(BaseModel):
    id: str
    passport_number: str
    residence_card_number: str
    receipt_number: str
    effective_date: date
    passport_number_list: str
    departure_date: date
    entry_date: date
    port_of_landing: str
    length_of_stay: int
    accompany: bool
    place_of_visa_application: str
    prev_entry_count: int
    prev_entry_date: date
    prev_departure_date: date
    commited_offense: bool
    commited_offense_details: str
    forced_departure_count: int
    recent_forced_departure_date: date

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class DeleteEmployeeImmigrationDetails(BaseModel):
    id: str
    employee: str

    class config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }


class CreateEmployeeSchoolWorkHistory(BaseModel):
    employee: str
    work_history: str
    school_history: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class UpdateEmployeeSchoolWorkHistory(BaseModel):
    id: str
    work_history: str
    school_history: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class DeleteEmployeeSchoolWorkHistory(BaseModel):
    id: str
    employee: str

    class config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }


class CreateEmployeeRelatives(BaseModel):
    employee: str
    relatives: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class UpdateEmployeeRelatives(BaseModel):
    id: str
    relatives: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null

        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        return values


class DeleteEmployeeRelatives(BaseModel):
    id: str
    employee: str


class CreateEmployeeQualifications(BaseModel):
    employee: str
    qualifications: str
    prev_technical_training: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null

        for value in values:
            if len(str(values.get(value))) == 0:
                raise ValueError(f'Form has an empty field. : {value}')

        return values
