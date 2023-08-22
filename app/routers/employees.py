from datetime import datetime
import shutil
import os
import time
import json

from typing import List, Type
from dotenv import load_dotenv

# tortoise
from tortoise.contrib.fastapi import HTTPNotFoundError

# models
from app.models.user import User, user_pydantic
from app.models.employee import Employee, employee_pydantic
from app.models.employee_immigration_details import Emp_Immigration_Details, emp_immigration_details_pydantic
from app.models.employee_relatives import Emp_Relatives, emp_relatives_pydantic
from app.models.employee_school_work_history import Emp_School_Work_History, emp_school_work_history_pydantic
from app.models.employee_qualifications import Emp_Qualification, emp_qualifications_pydantic

# pydantic schema
from app.models.employee_schema import DeleteEmployee, CreateEmployeeImmigrationDetails, CreateEmployeeRelatives, CreateEmployeeSchoolWorkHistory, CreateEmployeeQualifications

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, Form, UploadFile

# authentication
from app.auth.authentication import hash_password, token_generator, verify_password, verify_token_email

# email verification
from app.auth.email_verification import send_email

from app.helpers.s3_file_upload import upload_image_to_s3, generate_s3_url

# s3_upload_path = os.environ['AWS_PPS_STORAGE_URL'] + 'uploads/employees/img/'
s3_upload_folder = 'uploads/employees/img/'

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("/", responses={status.HTTP_201_CREATED: {"model": employee_pydantic}})
async def get_employees(user_email_token: str):
    # get the user email from the token
    # for more security later, we can use the user id instead of email
    # user_email = verify_token_email(user_email_token)

    # get the user id from the token # change this later to token id
    user = await User.get(email=user_email_token).values('id')

    employees = Employee.filter(disabled=False,
                                # user_id=user_id['id']).order_by('display_order').all()
                                user_id=user['id']).all()

    employee_list = await employee_pydantic.from_queryset(employees)

    return employee_list


@router.get("/employee_details")
async def get_employee_details(employee: str):
    try:
        # check if employee exists on 4 sub tables named employee_immigration_details, employee_relatives, employee_school_work_history, employee_qualifications

        # get employee id
        employee_id = await Employee.get(id=employee.employee_id).values('id')

        print(employee_id)
    except Exception as e:
        print("Error: ", e)

    return {'data': {}, 'msg':  'No employee detais found'}


@router.post("/add_employee", status_code=status.HTTP_201_CREATED)
async def create_employee(employee_json: str = Form(...), employee_image: UploadFile = File(...)):
    # emp_info = employee.dict(exclude_unset=True)

    employee_data = json.loads(employee_json)

    # remove employee id
    # del employee_data['id']

    # image = employee_image.read()

    is_file_image = employee_image.content_type.startswith('image')

    if not is_file_image:
        raise HTTPException(status_code=400, detail="File is not an image")

    now = datetime.now()
    image_name = employee_data['name_romaji'].split(
        ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + employee_image.filename.split('.')[-1]

    # s3_img_url = s3_upload_path + image_name
    s3_img_path = s3_upload_folder + image_name

    # upload to s3 bucket
    uploaded_file = upload_image_to_s3(employee_image, image_name)

    print("uploaded: ", uploaded_file)

    # generate url with the image name
    s3_read_url = generate_s3_url(s3_img_path, 'read')

    # append s3_read_url to employee_data
    employee_data['img_url'] = s3_read_url

    print("s3_read_url: ", s3_read_url)

    # confirm and get the user id
    user = await User.get(id=employee_data['user_id']).values('id')

    # make a json object called specified_skills_object that contains the specified skills above
    employee_data['specified_skills_object'] = json.dumps({
        "items": [
            {
                "id": 1,
                "from_date": employee_data['specified_skills_object_1_from'],
                "to_date": employee_data['specified_skills_object_1_to']
            },
            {
                "id": 2,
                "from_date": employee_data['specified_skills_object_2_from'],
                "to_date": employee_data['specified_skills_object_2_to']
            }
        ]
    })

    del employee_data['specified_skills_object_1_from']
    del employee_data['specified_skills_object_1_to']
    del employee_data['specified_skills_object_2_from']
    del employee_data['specified_skills_object_2_to']

    # # create employee
    emp_data = await Employee.create(**employee_data)

    new_employee = await employee_pydantic.from_tortoise_orm(emp_data)

    return new_employee

    # new_employee = await employee_pydantic.from_tortoise_orm(emp_data)

    # # print("Time taken: ", time.time() - start_time)

    # return {'data': new_employee, 'msg':  'Employee created successfully'}

# @router.post("/add_change_employee_image", status_code=status.HTTP_201_CREATED)
# async def add_change_employee_image(employee_id: str, image: UploadFile = File(...)):
#     employee = await Employee.get(id=employee_id).values('id','name_romaji')

#     # to avoid file name duplicates, lets concatenate datetime and user's name
#     now = datetime.now()
#     new_image_name = employee['name_romaji'].split('@')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + image.filename.split('.')[-1]

#     return ''


@router.put("/update_employee", status_code=status.HTTP_201_CREATED)
async def update_employee(employee_json: str = Form(...), employee_image: UploadFile = File(None)):
    # emp_info = employee.dict(exclude_unset=True)

    # if employee_image is string dont upload to s3 bucket
    if employee_image is not None:
        is_file_image = employee_image.content_type.startswith('image')

        if not is_file_image:
            raise HTTPException(status_code=400, detail="File is not an image")

        now = datetime.now()
        image_name = employee_data['name_romaji'].split(
            ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + employee_image.filename.split('.')[-1]

        # s3_img_url = s3_upload_path + image_name
        s3_img_path = s3_upload_folder + image_name

        # upload to s3 bucket
        uploaded_file = upload_image_to_s3(employee_image, image_name)

        print("uploaded: ", uploaded_file)

        # generate url with the image name
        s3_read_url = generate_s3_url(s3_img_path, 'read')

        # append s3_read_url to employee_data
        employee_data['img_url'] = s3_read_url

        print("s3_read_url: ", s3_read_url)

    employee_data = json.loads(employee_json)

    # check if employee_data['specified_skills_object_1_from'] exists
    if 'specified_skills_object_1_from' in employee_data:
        # make a json object called specified_skills_object that contains the specified skills above
        employee_data['specified_skills_object'] = json.dumps({
            "items": [
                {
                    "id": 1,
                    "from_date": employee_data['specified_skills_object_1_from'],
                    "to_date": employee_data['specified_skills_object_1_to']
                },
                {
                    "id": 2,
                    "from_date": employee_data['specified_skills_object_2_from'],
                    "to_date": employee_data['specified_skills_object_2_to']
                }
            ]
        })

        del employee_data['specified_skills_object_1_from']
        del employee_data['specified_skills_object_1_to']
        del employee_data['specified_skills_object_2_from']
        del employee_data['specified_skills_object_2_to']

        # del employee_data['specified_skills_object_1_from']
        # del employee_data['specified_skills_object_1_to']
        # del employee_data['specified_skills_object_2_from']
        # del employee_data['specified_skills_object_2_to']

    employee_data_copy = employee_data.copy()
    # remove id
    employee_data_copy.pop('id')

    await Employee.get(id=employee_data['id']).update(**employee_data_copy)

    updated_employee = await employee_pydantic.from_queryset_single(Employee.get(id=employee_data['id']))

    return updated_employee


@router.put("/delete_employees", status_code=status.HTTP_201_CREATED)
async def delete_employee(employees: DeleteEmployee):
    employees = employees.dict(exclude_unset=True)

    # update all employees in the list employees's disabled to true
    await Employee.filter(id__in=employees['employees']).update(disabled=True)
    # await Employee.filter(id__in=employe  es['ids']).delete()

    return employees['employees']

    # return {'msg': 'Employees deleted successfully.'}

# immigration details


async def immigration_details_exists(employee_id: str):
    details = await Emp_Immigration_Details.filter(employee_id=employee_id).first()
    return details is not None


@router.get("/immigration_details")
async def get_employee_immigration_details(employee_id: str):
    # check if there is immigration details exists
    exists = await immigration_details_exists(employee_id)
    if not exists:
        return {}

    employee_immigration_details = await Emp_Immigration_Details.get(employee_id=employee_id)

    return employee_immigration_details

    #  raise HTTPException(
    #         status_code=501, detail="Error loading employee immigration details")


@router.post("/create_employee_immigration_details", status_code=status.HTTP_201_CREATED)
async def create_employee_immigration_details(immigration_details_json: str = Form(...)) -> dict:
    immigration_details = json.loads(immigration_details_json)

    # delete contact_number
    del immigration_details['contact_number']

    immigration_data = await Emp_Immigration_Details.create(**immigration_details)

    new_emp_immigration_data = await emp_immigration_details_pydantic.from_tortoise_orm(immigration_data)

    return new_emp_immigration_data

    # return {'data': new_emp_immigration_data, 'msg':  'Employee immigration details created successfully.'}


@router.post("/create_employee_relatives", status_code=status.HTTP_201_CREATED)
async def create_employee_relatives(relatives: CreateEmployeeRelatives) -> dict:
    relatives_details = relatives.dict(exclude_unset=True)

    # replace employee to employee_id
    relatives_details['employee_id'] = relatives_details['employee']
    del relatives_details['employee']

    relatives_data = await Emp_Relatives.create(**relatives_details)

    new_relatives_data = await emp_relatives_pydantic.from_tortoise_orm(relatives_data)

    return {'data': new_relatives_data, 'msg': 'Employee relatives added.'}


@router.post("/create_employee_schoolwork_history", status_code=status.HTTP_201_CREATED)
async def create_employee_schoolwork_history(history: CreateEmployeeSchoolWorkHistory) -> dict:
    history_details = history.dict(exclude_unset=True)

    # replace employee to employee_id
    history_details['employee_id'] = history_details['employee']
    del history_details['employee']

    history_data = await Emp_School_Work_History.create(**history_details)

    new_history_data = await emp_school_work_history_pydantic.from_tortoise_orm(history_data)

    return {'data': new_history_data, 'msg': 'Employee school work history added.'}


@router.post("/create_employee_qualifications", status_code=status.HTTP_201_CREATED)
async def create_employee_qualifications(qualifications: CreateEmployeeQualifications) -> dict:
    qualifications_details = qualifications.dict(exclude_unset=True)

    # replace employee to employee_id
    qualifications_details['employee_id'] = qualifications_details['employee']
    del qualifications_details['employee']

    qualifications_data = await Emp_Qualification.create(**qualifications_details)

    new_qualifications_data = await emp_qualifications_pydantic.from_tortoise_orm(qualifications_data)

    return {'data': new_qualifications_data, 'msg': 'Employee qualifications added.'}
