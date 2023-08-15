from datetime import datetime
import shutil
import os
import time

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
from app.models.employee_schema import CreateEmployee, CreateEmployeeImmigrationDetails, CreateEmployeeRelatives, CreateEmployeeSchoolWorkHistory, CreateEmployeeQualifications

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, UploadFile

# authentication
from app.auth.authentication import hash_password, token_generator, verify_password, verify_token_email

# email verification
from app.auth.email_verification import send_email

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

    employees = Employee.filter(
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


@router.post("/create_employee", status_code=status.HTTP_201_CREATED)
async def create_employee(employee: CreateEmployee, image: UploadFile = File(...)) -> dict:
    # start_time = time.time()

    emp_info = employee.dict(exclude_unset=True)

    print(f"email: {emp_info['user_email']}")

    user = await User.get(email=emp_info['user_email']).values('id')

    # add user id to emp info
    emp_info['user_id'] = user['id']
    # remove user email from emp info
    emp_info.pop('user_email')

    print(f"emp_info: {emp_info}")

    # create employee
    emp_data = await Employee.create(**emp_info)

    new_employee = await employee_pydantic.from_tortoise_orm(emp_data)

    # print("Time taken: ", time.time() - start_time)

    return {'data': new_employee, 'msg':  'Employee created successfully'}

# @router.post("/add_change_employee_image", status_code=status.HTTP_201_CREATED)
# async def add_change_employee_image(employee_id: str, image: UploadFile = File(...)):
#     employee = await Employee.get(id=employee_id).values('id','name_romaji')
    
#     # to avoid file name duplicates, lets concatenate datetime and user's name
#     now = datetime.now()
#     new_image_name = employee['name_romaji'].split('@')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + image.filename.split('.')[-1]
    
#     return ''


@router.post("/update_employee", status_code=status.HTTP_201_CREATED)
async def update_employee(employee: CreateEmployee) -> dict:
    emp_info = employee.dict(exclude_unset=True)

    print(f"email: {emp_info['user_email']}")

    user = await User.get(email=emp_info['user_email']).values('id')

    emp_data = await Employee.get(id=emp_info['id']).update(**emp_info)

    employee_id = emp_info['id']

    new_emp_data = await employee_pydantic.from_queryset_single(Employee.get(id=employee_id))

    return {"data": new_emp_data, "msg": 'Employee Updated.'}


@router.post("/create_employee_immigration_details", status_code=status.HTTP_201_CREATED)
async def create_employee_immigration_details(immigration_details: CreateEmployeeImmigrationDetails) -> dict:
    immigration_details = immigration_details.dict(exclude_unset=True)

    # replace employee to employee_id
    immigration_details['employee_id'] = immigration_details['employee']
    del immigration_details['employee']

    immigration_data = await Emp_Immigration_Details.create(**immigration_details)

    new_emp_immigration_data = await emp_immigration_details_pydantic.from_tortoise_orm(immigration_data)

    return {'data': new_emp_immigration_data, 'msg':  'Employee immigration details created successfully.'}


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
