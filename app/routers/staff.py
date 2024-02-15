import json
import os
import io
import re
import chardet
import calendar
import pandas as pd
import requests
import pytz

from typing import List, Type
from datetime import datetime, timedelta, timezone, time

# env
from dotenv import load_dotenv


# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

# models
from app.models.user import User
from app.models.staff import Staff, staff_pydantic, staffSelect_pydantic
from app.models.staff_shift import Staff_Shift, staff_shift_pydantic
from app.models.leave_request import Leave_Request, leave_request_pydantic

# helpers
from app.helpers.zipfile import zipfiles
from app.helpers.generate_pdf import fill_pdf_contract
from app.helpers.onedrive import read_from_onedrive, upload_file_to_onedrive
from app.helpers.datetime import adjust_time
from app.helpers.calculations import calculate_night_hours, calculate_single_night_shift, is_holiday

# notifications
from app.routers.notifications import create_and_broadcast_notification

# s3
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url, upload_image_to_s3, is_file_exists
from app.helpers.datetime import convert_to_js_compatible_format

# schema
from app.models.staff_schema import StaffLicense, LicenseData, StaffLoginCredentials
from app.models.email_schema import EmailDetails

from tempfile import NamedTemporaryFile

# auth
from app.auth.authentication import hash_password, staff_token_generator, verify_token_staff_code


from tortoise.expressions import Q
from tortoise.functions import Sum, Count


# one drive
# from app.helpers.onedrive import get_access_token
# import httpx

s3_staffimage_upload_folder = 'uploads/staff/img/'

s3_staffbankcard_upload_folder = 'uploads/staff/bank_img/'
s3_staffresidencecard_upload_folder = 'uploads/staff/residencecard_img/'
s3_staffpassport_upload_folder = 'uploads/staff/passport_img/'

s3_license_upload_folder = 'uploads/staff/pdf/'
s3_contracts_folder = 'uploads/staff/contracts/'

router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
    responses={404: {"some_description": "Not found"}}
)

load_dotenv()


@router.get("")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_staff(staff_group: str):
    # get the user email from the token
    # for more security later, we can use the user id instead of email
    # user_email = verify_token_email(user_email_token)

    staff = Staff.filter(disabled=False).exclude(Q(zaishoku_joukyou__icontains="退職") | Q(zaishoku_joukyou__icontains="退社済")).order_by(
        'staff_code').all()

    staff_list = await staff_pydantic.from_queryset(staff)

    # convert licenses and bank_card_iamges to json
    # check first if there is licenses or bank_card_images
    for staff in staff_list:
        if staff.licenses is not None:
            staff.licenses = json.loads(staff.licenses)

        if staff.bank_card_images is not None:
            staff.bank_card_images = json.loads(staff.bank_card_images)

        if staff.passport_details is not None:
            staff.passport_details = json.loads(staff.passport_details)

        if staff.residence_card_details is not None:
            # print(staff.residence_card_details)
            staff.residence_card_details = json.loads(
                staff.residence_card_details)

    return staff_list


@router.post("/login")
async def login_staff(login_info: StaffLoginCredentials):
    token = await staff_token_generator(login_info.staff_code, login_info.password)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid staff code or password.",
            # headers={"WWW-Authenticate": "Basic"},
            headers={"WWW-Authenticate": "Bearer"}
        )

    # print(token)
    return token


@router.get("/get_staff_info")
async def get_staff_info(token: str):
    staff = await verify_token_staff_code(token)

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # print(staff)
    return staff


@router.get("/staff_select")
async def get_staff_select():

    # same as staff but only take id, english_name, japanese_name, staff_group, duty_type
    staff = Staff.filter(disabled=False).exclude(Q(zaishoku_joukyou__icontains="退職") | Q(zaishoku_joukyou__icontains="退社済")).order_by(
        'staff_code').all()

    staff_list = await staffSelect_pydantic.from_queryset(staff)

    return staff_list


@router.post("/add_staff")
async def create_staff(staff_json: str = Form(...), staff_image: UploadFile = File(None), licenses: List[UploadFile] = File(None), bank_card_front: UploadFile = File(None), bank_card_back: UploadFile = File(None), passport_file: UploadFile = File(None), residence_card_front: UploadFile = File(None), residence_card_back: UploadFile = File(None)):
    staff_data = json.loads(staff_json)

    # file_names = []
    now = datetime.now()
    if licenses is not None:
        for file in licenses:
            # You can access file properties like filename, content type, and content
            # file_names.append(file.filename)

            # create a new filename string with file name plus timestamp
            new_file_name = file.filename.split(
                '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]
            # upload to s3 bucket
            uploaded_file = upload_file_to_s3(
                file, new_file_name, s3_license_upload_folder)

            s3_file_path = s3_license_upload_folder + new_file_name

            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # the license list has the same length as the staff_data's licenses list please change the value to the new file name in the staff_data
            staff_data['licenses'][licenses.index(file)]['file'] = s3_read_url
            # replace the file object with the s3 url

        staff_data['licenses'] = json.dumps(staff_data['licenses'])

    # staff profile photo
    if staff_image is not None:
        image_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + staff_image.filename.split('.')[-1]
        # s3_img_url = s3_upload_path + image_name
        s3_img_path = s3_staffimage_upload_folder + image_name
        # upload to s3 bucket
        uploaded_file = upload_image_to_s3(staff_image, image_name, "img")
        s3_read_url = generate_s3_url(s3_img_path, 'read')
        # append s3_read_url to employee_data
        staff_data['img_url'] = s3_read_url

    # object for bank card images, if the bank_card_images is empty, we will create a new dict
    bank_card_images = staff_data['bank_card_images'] if staff_data['bank_card_images'] != '' else {
    }

    if bank_card_front is not None:
        bank_card_front_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + bank_card_front.filename.split('.')[-1]
        s3_bankimage_path_front = s3_staffbankcard_upload_folder + bank_card_front_name
        uploaded_file_front = upload_image_to_s3(
            bank_card_front, bank_card_front_name, "bank_img")
        card_front_read_url = generate_s3_url(s3_bankimage_path_front, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images['front'] = card_front_read_url

    if bank_card_back is not None:
        bank_card_back_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + bank_card_back.filename.split('.')[-1]
        s3_bankimage_path_back = s3_staffbankcard_upload_folder + bank_card_back_name
        uploaded_file_back = upload_image_to_s3(
            bank_card_back, bank_card_back_name, "bank_img")
        card_back_read_url = generate_s3_url(s3_bankimage_path_back, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images['back'] = card_back_read_url

    # stringify bank_card_images
    staff_data['bank_card_images'] = json.dumps(bank_card_images)

    # residence card front and back
    if residence_card_front is not None:
        residence_card_front_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + residence_card_front.filename.split('.')[-1]
        s3_residencecard_path_front = s3_staffresidencecard_upload_folder + \
            residence_card_front_name

        uploaded_file_front = upload_image_to_s3(
            residence_card_front, residence_card_front_name, "residencecard_img")
        card_front_read_url = generate_s3_url(
            s3_residencecard_path_front, 'read')

        staff_data['residence_card_details']['front'] = card_front_read_url

    if residence_card_back is not None:
        residence_card_back_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + residence_card_back.filename.split('.')[-1]
        s3_residencecard_path_back = s3_staffresidencecard_upload_folder + \
            residence_card_back_name
        uploaded_file_back = upload_image_to_s3(
            residence_card_back, residence_card_back_name, "residencecard_img")
        card_back_read_url = generate_s3_url(
            s3_residencecard_path_back, 'read')

        staff_data['residence_card_details']['back'] = card_back_read_url

    # append residence_card_details
    staff_data['residence_card_details'] = json.dumps(
        staff_data['residence_card_details'])

    # passport details with file
    if passport_file is not None:
        passport_file_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_passport_%Y%m%d_%H%M%S") + '.' + passport_file.filename.split('.')[-1]
        s3_passport_path = s3_staffpassport_upload_folder + passport_file_name
        uploaded_file = upload_image_to_s3(
            passport_file, passport_file_name, "passport_img")
        passport_read_url = generate_s3_url(s3_passport_path, 'read')

        # add the url to the passport_details dict
        staff_data['passport_details']['file'] = passport_read_url

    # append passport_details
    staff_data['passport_details'] = json.dumps(staff_data['passport_details'])

    # create staff
    staff = await Staff.create(**staff_data)

    new_staff = await staff_pydantic.from_tortoise_orm(staff)
    # new_staff = await Staff.get(id=staff.id).values()

    # if there is only license
    if licenses is not None:
        # convert licenses to json
        new_staff.licenses = json.loads(new_staff.licenses)
    else:
        new_staff.licenses = []

    new_staff.bank_card_images = json.loads(
        new_staff.bank_card_images)

    new_staff.residence_card_details = json.loads(
        new_staff.residence_card_details)

    new_staff.passport_details = json.loads(
        new_staff.passport_details)

    return new_staff


@router.put("/update_staff")
async def update_staff(staff_json: str = Form(...), staff_image: UploadFile = File(None), licenses: List[UploadFile] = File(None),  bank_card_front: UploadFile = File(None), bank_card_back: UploadFile = File(None), passport_file: UploadFile = File(None), residence_card_front: UploadFile = File(None), residence_card_back: UploadFile = File(None)):
    staff_data = json.loads(staff_json)

    now = datetime.now()
    if licenses is not None:
        for file in licenses:
            # You can access file properties like filename, content type, and content
            # file_names.append(file.filename)

            # create a new filename string with file name plus timestamp
            new_file_name = file.filename.split(
                '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]
            # upload to s3 bucket
            uploaded_file = upload_file_to_s3(
                file, new_file_name, s3_license_upload_folder)

            s3_file_path = s3_license_upload_folder + new_file_name

            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # the license list has the same length as the staff_data's licenses list please change the value to the new file name in the staff_data
            staff_data['licenses'][licenses.index(file)]['file'] = s3_read_url
            # replace the file object with the s3 url

        staff_data['licenses'] = json.dumps(staff_data['licenses'])

    if staff_image is not None:
        now = datetime.now()
        image_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + staff_image.filename.split('.')[-1]

        # s3_img_url = s3_upload_path + image_name
        s3_img_path = s3_staffimage_upload_folder + image_name

        # upload to s3 bucket
        uploaded_file = upload_image_to_s3(staff_image, image_name, "img")

        # print("uploaded: ", uploaded_file)

        s3_read_url = generate_s3_url(s3_img_path, 'read')

        # append s3_read_url to employee_data
        staff_data['img_url'] = s3_read_url

        # print("s3_read_url: ", s3_read_url)

    # check if staff_data['bank_card_images'] exists
    if 'bank_card_images' in staff_data:

        # object for bank card images, if the bank_card_images is empty, we will create a new dict
        bank_card_images = staff_data['bank_card_images'] if staff_data['bank_card_images'] != '' else {
        }

    if bank_card_front is not None:
        bank_card_front_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + bank_card_front.filename.split('.')[-1]
        s3_bankimage_path_front = s3_staffbankcard_upload_folder + bank_card_front_name
        uploaded_file_front = upload_image_to_s3(
            bank_card_front, bank_card_front_name, "bank_img")
        card_front_read_url = generate_s3_url(s3_bankimage_path_front, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images['front'] = card_front_read_url

    if bank_card_back is not None:
        bank_card_back_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + bank_card_back.filename.split('.')[-1]
        s3_bankimage_path_back = s3_staffbankcard_upload_folder + bank_card_back_name
        uploaded_file_back = upload_image_to_s3(
            bank_card_back, bank_card_back_name, "bank_img")
        card_back_read_url = generate_s3_url(s3_bankimage_path_back, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images['back'] = card_back_read_url

    # stringify bank_card_images
    if 'bank_card_images' in staff_data:
        staff_data['bank_card_images'] = json.dumps(bank_card_images)

    # residence card front and back
    if residence_card_front is not None:
        residence_card_front_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + residence_card_front.filename.split('.')[-1]
        s3_residencecard_path_front = s3_staffresidencecard_upload_folder + \
            residence_card_front_name

        uploaded_file_front = upload_image_to_s3(
            residence_card_front, residence_card_front_name, "residencecard_img")
        card_front_read_url = generate_s3_url(
            s3_residencecard_path_front, 'read')

        staff_data['residence_card_details']['front'] = card_front_read_url

    if residence_card_back is not None:
        residence_card_back_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + residence_card_back.filename.split('.')[-1]
        s3_residencecard_path_back = s3_staffresidencecard_upload_folder + \
            residence_card_back_name
        uploaded_file_back = upload_image_to_s3(
            residence_card_back, residence_card_back_name, "residencecard_img")
        card_back_read_url = generate_s3_url(
            s3_residencecard_path_back, 'read')

        staff_data['residence_card_details']['back'] = card_back_read_url

    # append
    if 'residence_card_details' in staff_data:
        # append residence_card_number
        # if 'residence_card_number' in staff_data:
        #     # add the number to the residence_card_details dict
        #     staff_data['residence_card_details']['number'] = staff_data['residence_card_number']

        staff_data['residence_card_details'] = json.dumps(
            staff_data['residence_card_details'])

    # passport details with file
    if passport_file is not None:
        passport_file_name = staff_data['english_name'].split(
            ' ')[0] + now.strftime(
            "_passport_%Y%m%d_%H%M%S") + '.' + passport_file.filename.split('.')[-1]
        s3_passport_path = s3_staffpassport_upload_folder + passport_file_name
        uploaded_file = upload_image_to_s3(
            passport_file, passport_file_name, "passport_img")
        passport_read_url = generate_s3_url(s3_passport_path, 'read')

        # add the url to the passport_details dict
        staff_data['passport_details']['file'] = passport_read_url

    # append
    if 'passport_details' in staff_data:
        # append passport_number
        # if 'passport_number' in staff_data:
        #     # add the number to the passport_details dict
        #     staff_data['passport_details']['number'] = staff_data['passport_number']

        staff_data['passport_details'] = json.dumps(
            staff_data['passport_details'])

    staff_data_copy = staff_data.copy()

    staff_data_copy.pop('id')
    # new jan 29 2024 #temporarily added passport_number and residence_card_number individually pop the two of them but check if each of them exists
    # if 'passport_number' in staff_data_copy:
    #     staff_data_copy.pop('passport_number')

    # if 'residence_card_number' in staff_data_copy:
    #     staff_data_copy.pop('residence_card_number')

    # update staff

    # print(staff_data_copy)

    await Staff.filter(id=staff_data['id']).update(**staff_data_copy)

    updated_staff = await staff_pydantic.from_queryset_single(Staff.get(id=staff_data['id']))

    # if there is only license
    if licenses is not None:
        # convert licenses to json
        updated_staff.licenses = json.loads(updated_staff.licenses)
    else:
        updated_staff.licenses = []

    updated_staff.bank_card_images = json.loads(
        updated_staff.bank_card_images)

    updated_staff.residence_card_details = json.loads(
        updated_staff.residence_card_details)

    updated_staff.passport_details = json.loads(
        updated_staff.passport_details)

    return updated_staff

# add documents in staff


@router.put("/add_document")
async def add_document_staff(staff_id: str = Form(...), document_type: str = Form(...), document_image: UploadFile = File(None)):
    allowed_document_types = ['bank_card_front', 'bank_card_back',
                              'residence_card_back', 'residence_card_front', 'passport']

    if document_type not in allowed_document_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type.",
        )

    now = datetime.now()
    # if the document type is bank_card
    if document_type == 'bank_card_front':
        document_name = now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + document_image.filename.split('.')[-1]
        s3_document_path = s3_staffbankcard_upload_folder + document_name
        uploaded_file = upload_image_to_s3(
            document_image, document_name, "bank_img")
        document_read_url = generate_s3_url(s3_document_path, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images = await Staff.get(id=staff_id).values('bank_card_images')
        bank_card_images = json.loads(bank_card_images['bank_card_images'])

        bank_card_images['front'] = document_read_url

        # stringify bank_card_images
        bank_card_images = json.dumps(bank_card_images)

        await Staff.filter(id=staff_id).update(bank_card_images=bank_card_images)
    elif document_type == 'bank_card_back':
        document_name = now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + document_image.filename.split('.')[-1]
        s3_document_path = s3_staffbankcard_upload_folder + document_name
        uploaded_file = upload_image_to_s3(
            document_image, document_name, "bank_img")
        document_read_url = generate_s3_url(s3_document_path, 'read')

        # add the url to the bank_card_images dict make sure it is json friendly
        bank_card_images = await Staff.get(id=staff_id).values('bank_card_images')
        bank_card_images = json.loads(bank_card_images['bank_card_images'])

        bank_card_images['back'] = document_read_url

        # stringify bank_card_images
        bank_card_images = json.dumps(bank_card_images)

        await Staff.filter(id=staff_id).update(bank_card_images=bank_card_images)
    elif document_type == 'residence_card_front':
        document_name = now.strftime(
            "_front_%Y%m%d_%H%M%S") + '.' + document_image.filename.split('.')[-1]
        s3_document_path = s3_staffresidencecard_upload_folder + document_name
        uploaded_file = upload_image_to_s3(
            document_image, document_name, "residencecard_img")
        document_read_url = generate_s3_url(s3_document_path, 'read')

        # add the url to the residence_card_details dict make sure it is json friendly
        residence_card_details = await Staff.get(id=staff_id).values('residence_card_details')
        residence_card_details = json.loads(
            residence_card_details['residence_card_details'])

        residence_card_details['front'] = document_read_url

        # stringify residence_card_details
        residence_card_details = json.dumps(residence_card_details)

        await Staff.filter(id=staff_id).update(residence_card_details=residence_card_details)
    elif document_type == 'residence_card_back':
        document_name = now.strftime(
            "_back_%Y%m%d_%H%M%S") + '.' + document_image.filename.split('.')[-1]
        s3_document_path = s3_staffresidencecard_upload_folder + document_name
        uploaded_file = upload_image_to_s3(
            document_image, document_name, "residencecard_img")
        document_read_url = generate_s3_url(s3_document_path, 'read')

        # add the url to the residence_card_details dict make sure it is json friendly
        residence_card_details = await Staff.get(id=staff_id).values('residence_card_details')
        residence_card_details = json.loads(
            residence_card_details['residence_card_details'])

        residence_card_details['back'] = document_read_url

        # stringify residence_card_details
        residence_card_details = json.dumps(residence_card_details)

        await Staff.filter(id=staff_id).update(residence_card_details=residence_card_details)
    elif document_type == 'passport':
        document_name = now.strftime(
            "_passport_%Y%m%d_%H%M%S") + '.' + document_image.filename.split('.')[-1]
        s3_document_path = s3_staffpassport_upload_folder + document_name
        uploaded_file = upload_image_to_s3(
            document_image, document_name, "passport_img")
        document_read_url = generate_s3_url(s3_document_path, 'read')

        # add the url to the passport_details dict
        passport_details = await Staff.get(id=staff_id).values('passport_details')
        passport_details = json.loads(passport_details['passport_details'])

        passport_details['file'] = document_read_url

        # stringify passport_details
        passport_details = json.dumps(passport_details)

        await Staff.filter(id=staff_id).update(passport_details=passport_details)

    # get the updated staff
    updated_staff = await staff_pydantic.from_queryset_single(Staff.get(id=staff_id))

    updated_staff.bank_card_images = json.loads(
        updated_staff.bank_card_images)

    updated_staff.residence_card_details = json.loads(
        updated_staff.residence_card_details)

    updated_staff.passport_details = json.loads(
        updated_staff.passport_details)

    return updated_staff


@router.put("/delete_staff")
async def delete_staff(staff_json: str = Form(...)):
    staff_data = json.loads(staff_json)

    # update all employees in the list employees's disabled to true
    await Staff.filter(id__in=staff_data['staff']).update(disabled=True)
    # await Employee.filter(id__in=employe  es['ids']).delete()

    return staff_data['staff']

    # return {'msg': 'Employees deleted successfully.'}


@router.get('/generate')
async def generate_contracts(staff_id: str):
    staff = await Staff.get(id=staff_id).values('english_name')

    staff_name = staff['english_name']
    now = datetime.now()
    formatted_now = now.strftime("_%Y")

    contract_file_name = staff_name.replace(" ", "") + formatted_now + '.pdf'

    # check aws s3 bucket if this file exist.
    # if exist, return the file url
    # if not exist, create the file and upload to s3 bucket

    # check if file exist
    file_path = s3_contracts_folder + contract_file_name

    if is_file_exists(file_path):
        # print("file exists")
        return generate_s3_url(file_path, 'read')
    else:
        pdf = fill_pdf_contract(staff)

    # open the pdf file in binary mode
    # with open(pdf, 'rb') as file:
    # zipf = zipfiles(pdf, f'files_{staff_id}')

    return pdf[0]


@router.get('/download')
async def download_staff_list():
    # get all staff which is ordered by zaishoku_joukyou
    staff = await Staff.filter(disabled=False).order_by('staff_code').values(
        'affiliation', 'staff_code', 'english_name', 'japanese_name', 'nickname', 'nationality', 'join_date',
        'leave_date', 'postal_code', 'prefecture', 'municipality', 'town',
        'building', 'phone_number', 'personal_email', 'work_email', 'koyou_keitai', 'zaishoku_joukyou',
    )

    df = pd.DataFrame(staff)

    # headers = ["affiliation", "staff_code", "english_name", "japanese_name", "nickname", "nationality", "join_date",
    #            "leave_date", "postal_code", "prefecture", "municipality", "town",
    #            "building", "phone_number", "personal_email", "work_email", "koyou_keitai", "zaishoku_joukyou"]

    # change column headers
    headers = ["所属", "社員番号", "NAME", "職員名", "ニックネーム", "国籍 ", "入社年月日", "退社年月日", "郵便番号",
               "都道府県", "市区町村", "町名以下", "建物名", "職員電話番号", "個人Eメールアドレス", "職員Eメールアドレス", "雇用形態", "在職状況"]

    # Create a temporary Excel file
    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        excel_writer = pd.ExcelWriter(tmp_file.name, engine='xlsxwriter')
        df.to_excel(excel_writer, index=False, header=headers)

        # Get the xlsxwriter workbook and worksheet objects
        workbook = excel_writer.book
        # You may need to adjust the sheet name
        worksheet = excel_writer.sheets['Sheet1']

        # Adjust column widths based on content
        # for i, col in enumerate(headers):
        #     column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)  # +2 for padding
        #     worksheet.set_column(i, i, column_len)

        # Adjust column widths based on content
        for i in range(len(headers)):
            max_len = df.iloc[:, i].astype(str).str.len().max()
            column_len = max(max_len, len(headers[i]) + 2)  # +2 for padding
            worksheet.set_column(i, i, column_len)

        # FFD580
        format_orange = workbook.add_format(
            {'bg_color': '#FFD580'})  # Red background
        worksheet.conditional_format(
            1,  # Starting row (assuming header is in row 1)
            headers.index('在職状況'),  # Column index of '雇用形態'
            df.shape[0],  # Number of rows
            headers.index('在職状況'),  # Column index of '雇用形態'
            {'type': 'text', 'criteria': 'containing',
                'value': '退社済', 'format': format_orange}
        )

        excel_writer.close()  # Close the ExcelWriter to save the Excel file

    # Return the Excel file as a response
    response = FileResponse(
        tmp_file.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=staff.xlsx"

    return response

# Define a function to apply row coloring


def highlight_rows(row):
    if row["zaishoku_joukyou"] == "退社済":
        return ['background-color: gray'] * len(row)
    else:
        return [''] * len(row)


@router.get("/shifts")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_all_schedule():
    # add staffs japanese name and english name in the values

    # shifts = await Staff_Shift.all().values()
    # filter shift list by current month only
    # shifts = await Staff_Shift.filter(start__month=datetime.now().month).values()

    # timezone = pytz.UTC
    now = datetime.now()

    # First day of the current month
    first_day_of_current_month = datetime(now.year, now.month, 1,
                                          #   tzinfo=timezone
                                          )

    # First day of the month after the next month
    if now.month == 12:
        first_day_of_month_after_next = datetime(now.year + 1, 2, 1,
                                                 #  tzinfo=timezone
                                                 )
    else:
        first_day_of_month_after_next = datetime(now.year + (now.month // 12), now.month % 12 + 2, 1,
                                                 #  tzinfo=timezone
                                                 )

    # Last day of the next month (one second before the first day of the month after next)
    last_day_of_next_month = first_day_of_month_after_next - \
        timedelta(seconds=1)

    # Fetch shifts for the current and next month
    # shifts = await Staff_Shift.filter(
    #     Q(start__gte=first_day_of_current_month) & Q(
    #         start__lt=first_day_of_month_after_next)
    # ).values()

    # get all shifts
    shifts = await Staff_Shift.all().values()

    return shifts


@router.get("/shift_by_staff")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_schedule_by_staff(staff_name: str):

    # timezone = pytz.UTC
    now = datetime.now()

    # First day of the current month
    first_day_of_current_month = datetime(now.year, now.month, 1)

    # First day of the month after the next month
    if now.month == 12:
        first_day_of_month_after_next = datetime(now.year + 1, 2, 1)
    else:
        first_day_of_month_after_next = datetime(
            now.year + (now.month // 12), now.month % 12 + 2, 1)

    # Last day of the next month (one second before the first day of the month after next)
    last_day_of_next_month = first_day_of_month_after_next - \
        timedelta(seconds=1)

    # shifts = await Staff_Shift.filter(start__month=datetime.now().month, staff__icontains=staff_name).values("id", "staff", "patient", "service_type", "service_details", "start", "end", "duration")
    shifts = await Staff_Shift.filter(Q(start__gte=first_day_of_current_month) & Q(start__lt=first_day_of_month_after_next), staff__icontains=staff_name).values("id", "staff", "patient", "service_type", "service_details", "start", "end", "duration")

    return shifts


@router.get("/upcoming_shift_by_staff")
async def get_latest_shift_by_staff(staff_name: str):
    # Get the current time
    current_time = datetime.now()

    # Query for the next shift for the given staff that starts after the current time
    # It will fetch the nearest future shift irrespective of the date
    next_shift = await Staff_Shift.filter(staff__icontains=staff_name, start__gte=current_time).order_by('start').first()

    if next_shift:
        return next_shift
    else:
        return {}

# ============================= STAFF SHIFT HTTP ENDPOINT ============================= #


@router.post("/import_staff_shift")
async def import_staff_shift(import_file: UploadFile = File(...)):
    # Check if the file is a CSV
    if not import_file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format")

    content = await import_file.read()

    # Detect the file encoding
    result = chardet.detect(content)
    encoding = result['encoding']

    columns_to_read = ['ヘルパー名', '日付', '利用者',
                       '業務種別', 'サービス内容', '開始時間', '終了時間', '提供時間（分）']

    # Read the file into a DataFrame
    df = pd.read_csv(io.StringIO(content.decode(encoding)), usecols=columns_to_read, delimiter=',', index_col=None,
                     encoding=encoding, header=0, names=['ヘルパー名', '日付', '曜日', '利用者', '業務種別', 'サービス内容', '開始時間', '終了時間', '提供時間（分）', '備考'])

    # Rename the columns after reading the CSV
    df.rename(
        columns={
            'ヘルパー名': 'staff',
            '日付': 'date',
            '利用者': 'patient',
            '業務種別': 'service_type',
            'サービス内容': 'service_details',
            '開始時間': 'start',
            '終了時間': 'end',
            '提供時間（分）': 'duration'
        },
        inplace=True,
    )

    # Remove '分' from the 'duration' values and convert to integer
    df['duration'] = df['duration'].str.replace('分', '').astype(int)

    # Assuming the '日付' column contains the day of the month and needs to be combined with the year and month from the filename
    # Example: Replace with actual logic to extract year and month from file name
    file_year_month = import_file.filename.rsplit('.', 1)[0]
    # print(file_year_month)
    match = re.search(r'(\d{6})$', file_year_month)
    if match:
        year_month = match.group(1)
        year = int(year_month[:4])
        month = int(year_month[4:])
    else:
        raise ValueError("Year and month not found in the filename")

    # Combine year, month, and day to create a full date
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%d').apply(
        lambda x: x.replace(year=year, month=month))

    df['start'] = df.apply(lambda row: adjust_time(
        row['date'], row['start']), axis=1)
    df['end'] = df.apply(lambda row: adjust_time(
        row['date'], row['end']), axis=1)

    # Determine the range of dates for the given month and year
    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day)

    # Adjust end_date to the end of the last day of the month
    end_date = end_date.replace(
        hour=23, minute=59, second=59, microsecond=999999)

    # Delete existing records for that month and year
    await Staff_Shift.filter(
        start__gte=start_date,
        start__lte=end_date
    ).delete()

    # the staff/helper column name supposedly to be matched with the staff model,
    #  however for now we can use only the name, we will not make a connection yet.
    # later on, it might be needed

    # insert data in chunks
    for chunk in range(0, df.shape[0], 150):  # Adjust chunk size as needed
        staff_shift_data = df.iloc[chunk:chunk + 150].to_dict(orient='records')
        staff_shift_objects = [Staff_Shift(**data)
                               for data in staff_shift_data]
        # Bulk create using Tortoise ORM
        await Staff_Shift.bulk_create(staff_shift_objects)

    return {"status": "success", "message": f"Successfully imported {len(df)} staff shifts."}


@router.post('/add_shift')
async def create_shift(staff_shift_json: str = Form(...)):
    shift_data = json.loads(staff_shift_json)

    staff_data = shift_data.pop('staff')
    # get id from staff_data
    staff_id = staff_data['id']

    # add staff_id on shift_data
    shift_data['staff_id'] = staff_id

    # print(shift_data)

    schedule = await Staff_Shift.create(**shift_data)

    new_schedule = await staff_shift_pydantic.from_tortoise_orm(schedule)

    return new_schedule


@router.put('/update_shift')
async def update_shift(staff_shift_json: str = Form(...)):
    # Parse the JSON string into a dictionary
    shift_data = json.loads(staff_shift_json)

    # Define the Tokyo timezone
    # tokyo_tz = ZoneInfo('Asia/Tokyo')

    # # Convert the millisecond timestamps to seconds, then to timezone-aware datetime objects
    # shift_data['start'] = datetime.fromtimestamp(shift_data['start'] / 1000.0, tz=tokyo_tz)
    # shift_data['end'] = datetime.fromtimestamp(shift_data['end'] / 1000.0, tz=tokyo_tz)

    shift_data['start'] = datetime.fromtimestamp(shift_data['start'] / 1000.0)
    shift_data['end'] = datetime.fromtimestamp(shift_data['end'] / 1000.0)

    # # Convert the timezone-aware datetime objects to UTC
    # shift_data['start'] = shift_data['start'].astimezone(timezone.utc)
    # shift_data['end'] = shift_data['end'].astimezone(timezone.utc)

    shift_id = shift_data['id']

    # remove date and id in shift_data
    shift_data.pop('date')
    shift_data.pop('id')

    await Staff_Shift.filter(id=shift_id).update(**shift_data)

    # If necessary, convert back to Tokyo time for the response
    # shift_data['start'] = shift_data['start'].astimezone(tokyo_tz)
    # shift_data['end'] = shift_data['end'].astimezone(tokyo_tz)

    # Return the updated data
    return shift_data


@router.delete('/delete_shift/{id}')
async def delete_shift(id: str):
    await Staff_Shift.filter(id=id).delete()

    return id

# shift confirmation by email


@router.post('/confirm_shift')
async def confirm_shift(email: EmailDetails):
    pass


def duration_str_to_minutes(duration_str):
    try:
        hours, minutes = map(int, duration_str.split(':'))
        return hours * 60 + minutes
    except ValueError:
        # Log the error or handle it as needed
        print(f"Invalid duration format: '{duration_str}'")
        return 0

# get the total number of work hours of shift


@router.get('/total_work_hours')
async def get_total_work_hours():
    # get all shifts duration of the staff of the start column which in current month and with service types that has only value of 重訪Ⅰ, 重訪Ⅱ, 重訪Ⅲ
    # Assuming your server is set to the same timezone as your database

    timezone = pytz.UTC
    now = datetime.now(timezone)

    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone)

    # Handling the increment of the month
    if now.month == 12:
        last_day_of_month = datetime(
            now.year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)
    else:
        last_day_of_month = datetime(
            now.year, now.month + 1, 1, tzinfo=timezone) - timedelta(seconds=1)

    # Debug: print the actual filter range
    # print(f"Filtering from {first_day_of_month} to {last_day_of_month}")

   # Now filter using the range
    durations = await Staff_Shift.filter(
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
        service_details__in=['重訪Ⅰ', '重訪Ⅱ', '重訪Ⅲ']
    ).values_list('duration', flat=True)

    # Summing the total minutes
    total_minutes = sum(int(d) for d in durations if d.isdigit())

    # Converting total minutes to hours
    total_hours = total_minutes / 60  # Use / for a floating-point result

    return {"total_hours": total_hours}


service_details_list = ['重訪Ⅰ', '重訪Ⅱ', '重訪Ⅲ', 'OFFICE事務作業']
group_home_patients_list = ['安宅 哲雄', '稲葉 博之', '梅田 扶美子',
                            '堺 宗太郎', '仙波 義弘', '安田 恵子', '岩崎 裕示', '三浦 八千代']


@router.post('/staff_current_records')
async def get_staff_current_records(staff_code: str, selected_date: str):
    # this will show records of the staff that are currently working :
    # Total Work hours based on Selected Month
    # Total Night Work hours based on Selected Month
    # Total Holiday Work hours based on Selected Month
    # (later) Total Transporation cost based on Selected Month

    # get the staff 'japanese name' by staff_code
    staff = await Staff.get(staff_code=staff_code, leave_date=None).values('japanese_name')

    # convert selected_date string to date object dont format it just make it into datetime
    # selected_date = datetime.strptime(selected_date, '%Y-%m-%d')
    # Split the string and convert year and month to integers
    year, month = map(int, selected_date.split('-'))
    selected_date = datetime(year, month, 1)

    # get the first and last day of the month
    timezone = pytz.UTC

    first_day_of_month = datetime(
        selected_date.year, selected_date.month, 1, tzinfo=timezone)

    # Handling the increment of the month
    if selected_date.month == 12:
        last_day_of_month = datetime(
            selected_date.year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)
    else:
        last_day_of_month = datetime(
            selected_date.year, selected_date.month + 1, 1, tzinfo=timezone) - timedelta(seconds=1)

    # total work hours
    duration = await Staff_Shift.filter(
        staff=staff['japanese_name'],
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
    ).exclude(
        # Excludes records with this specific service_details value
        service_details='☆★☆お休み希望☆★☆'
    ).filter(
        # Further filters the already filtered & excluded set
        service_details__in=service_details_list
    ).values_list('duration', flat=True)

    # Summing the total minutes
    wh_total_minutes = sum(int(d) for d in duration if d.isdigit())

    # Converting total minutes to hours
    total_work_hours = wh_total_minutes / 60  # Use / for a floating-point result

    # total night work hours
    # work hours starts from 22:00 to 05:00
    night_shifts = await Staff_Shift.filter(
        staff=staff['japanese_name'],
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
    ).exclude(
        # Excludes records with this specific service_details value
        service_details='☆★☆お休み希望☆★☆'
    ).exclude(
        patient__in=group_home_patients_list
    ).filter(
        # Further filters the already filtered & excluded set
        service_details__in=service_details_list
    ).values_list('start', 'end')

    filtered_night_shifts = []
    for start_datetime, end_datetime in night_shifts:
        # Extract time part for comparison
        start_time = start_datetime.time()
        end_time = end_datetime.time()

        # Define night time window
        night_start = time(22, 0)  # 22:00
        night_end = time(5, 0)    # 05:00

        # Check if shift falls within 22:00-05:00, accounting for midnight span
        if start_time >= night_start or end_time <= night_end or start_time < night_end:
            # For simplicity, we're adding the datetime objects directly but you may adjust as needed
            filtered_night_shifts.append((start_datetime, end_datetime))

    calculated_durations = calculate_night_hours(filtered_night_shifts)
    total_night_hours = sum(shift['overlap_hours']
                            for shift in calculated_durations)

    # total holiday work hours
    total_shifts = await Staff_Shift.filter(
        staff=staff['japanese_name'],
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
    ).exclude(
        # Excludes records with this specific service_details value
        service_details='☆★☆お休み希望☆★☆'
    ).filter(
        # Further filters the already filtered & excluded set
        service_details__in=service_details_list
    ).values_list('start', 'duration')

    total_holiday_minutes = 0
    for start, duration in total_shifts:
        if is_holiday(start):
            # print(start.strftime('%Y-%m-%d %H:%M:%S') +
            #       ' is a holiday' + ' duration: ' + str(duration))
            # Remove '分' from the duration string, convert to int
            duration_minutes = int(duration.replace('分', ''))
            # Add to total minutes
            total_holiday_minutes += duration_minutes

    total_holiday_hours = total_holiday_minutes / \
        60  # Convert total minutes to hours

    return {"total_hours": total_work_hours, "total_night_hours": total_night_hours, "total_holiday_hours": total_holiday_hours}


@router.post('/all_staff_time_calculation')
async def get_all_staff_time_calculation(selected_date: str = Form(...)):
    # Fetch all relevant shifts in bulk, assuming `Staff_Shift` has a foreign key to `Staff`
    # Convert selected_date string to a date range (first and last day of the month)
    year, month = map(int, selected_date.split('-'))
    timezone = pytz.UTC
    first_day_of_month = datetime(year, month, 1, tzinfo=timezone)
    last_day_of_month = datetime(year, month + 1, 1, tzinfo=timezone) - timedelta(
        seconds=1) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)

    # Fetch all shifts in the date range for all staff
    shifts = await Staff_Shift.filter(
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
    ).exclude(
        service_details='☆★☆お休み希望☆★☆'
    ).values('staff', 'patient', 'start', 'end', 'duration', 'service_details')

    # Fetch all staff with their codes and nationality
    staff_members = await Staff.filter(disabled=False).exclude(Q(zaishoku_joukyou__icontains="退職") | Q(zaishoku_joukyou__icontains="退社済")).all().values('japanese_name', 'staff_code', 'nationality')

    # Create a mapping from japanese_name to staff details
    staff_details_mapping = {
        staff['japanese_name']: staff for staff in staff_members}

    # Combine data
    combined_shifts = []
    for shift in shifts:
        staff_detail = staff_details_mapping.get(shift['staff'])
        if staff_detail:
            # Add staff_code and nationality to the shift information
            combined_shift = {
                **shift,
                'staff_code': staff_detail['staff_code'],
                'nationality': staff_detail['nationality']
            }
            combined_shifts.append(combined_shift)

    # Process shifts in Python to calculate metrics for each staff member
    staff_work_hours = {}
    staff_night_work_hours = {}
    staff_holiday_work_hours = {}

    all_patients = set()
    for shift in shifts:
        if shift["patient"] not in group_home_patients_list:
            all_patients.add(shift['patient'])

    # Step 2: Process shifts and initialize staff information with all patients
    # Initialize staff_patient_hours with all patients and special keys for every staff member
    staff_patient_hours = {
        staff['japanese_name']: {
            **{patient: 0 for patient in all_patients}, "group_home": 0, "group_home_stays": 0}
        for staff in staff_members
    }

    for shift in combined_shifts:
        # print(shift)
        staff_name = shift['staff']
        duration = int(shift['duration'].replace('分', ''))
        patient_name = shift['patient']
        hours = duration / 60.0  # Assuming duration is in minutes for this example

        night_hours = 0

        if shift['service_details'] in service_details_list:

            # total hours logic start

            # Aggregate hours for each staff member
            if staff_name not in staff_work_hours:
                staff_work_hours[staff_name] = hours
            else:
                # means that the staff_name is in the dictionary
                staff_work_hours[staff_name] += hours

            # total hours logic end

            # total night hours logic start
            if shift["patient"] not in group_home_patients_list:
                start = shift['start']
                end = shift['end']
                # Check if shift falls within 22:00-05:00, accounting for midnight span
                if start.time() >= time(22, 0) or end.time() <= time(5, 0) or start.time() < time(5, 0):
                    # calculate the night hours by this function
                    night_hours = calculate_single_night_shift(start, end)

                    # Aggregate night hours for each staff member
                    if staff_name not in staff_night_work_hours:
                        staff_night_work_hours[staff_name] = night_hours
                    else:
                        # means that the staff_name is in the dictionary
                        staff_night_work_hours[staff_name] += night_hours

            # total night hours logic

            # total holiday hours logic start

            if is_holiday(shift['start'].date()):
                # log all shift holidays with staff パダヤオ ジャービス
                # if shift["staff"] == "伊藤 美紀":
                #     print(shift["start"].strftime('%Y-%m-%d %H:%M:%S') + ' is a holiday' + ' duration: ' + str(duration))

                if staff_name not in staff_holiday_work_hours:
                    staff_holiday_work_hours[staff_name] = hours
                else:
                    # means that the staff_name is in the dictionary
                    staff_holiday_work_hours[staff_name] += hours

            # total holiday hours logic end

            # total work hours per patient logic start

            # Ensure staff entry exists
            if staff_name not in staff_patient_hours:
                staff_patient_hours[staff_name] = {
                    "group_home": 0, "group_home_stays": 0, }

            if shift["patient"] in group_home_patients_list:
                staff_patient_hours[staff_name]["group_home"] += hours
                # Increment the count only if the shift's start is 6 am
                if shift['start'].hour == 6:
                    staff_patient_hours[staff_name]["group_home_stays"] += 1
            else:
                # Ensure staff entry exists
                if staff_name not in staff_patient_hours:
                    staff_patient_hours[staff_name] = {}

                # Ensure patient entry exists for staff
                if patient_name not in staff_patient_hours[staff_name]:
                    staff_patient_hours[staff_name][patient_name] = 0

                # Add hours to the patient for the staff
                staff_patient_hours[staff_name][patient_name] += hours

            # total work hours per patient logic end

     # Initialize a list to hold the response data for each staff
    response_list = []
    for staff_name, patients_hours in staff_patient_hours.items():
        staff_detail = staff_details_mapping.get(staff_name, {})
        staff_info = {
            "staff": staff_name,
            "staff_code": staff_detail.get('staff_code', 'Unknown'),
            "nationality": staff_detail.get('nationality', 'Unknown'),
            "total_work_hours": round(staff_work_hours.get(staff_name, 0), 2),
            "night_work_hours": round(staff_night_work_hours.get(staff_name, 0), 2),
            "holiday_work_hours": round(staff_holiday_work_hours.get(staff_name, 0), 2),
        }
        staff_info.update({patient: round(hours, 2)
                          for patient, hours in patients_hours.items()})

        response_list.append(staff_info)

    response_list.sort(key=lambda x: x["staff_code"])
    return response_list


@router.post("/download_salarycalculation")
async def download_salary_calculation(records: str = Form(...)):
    records_data = json.loads(records)

    df = pd.DataFrame(records_data)

    headers = ["社員コード", "社員名", "国籍", "合計労働時間", "夜勤時間", "法定時間", "伊藤 和博", "山本 総来",
               "鈴木 孝幸", "櫛田 美知子", "岩谷 由紀子", "里光 真紀子", "研修408", "山本 愛", "Gホーム労働時間", "Gホーム宿泊回数"]

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        excel_writer = pd.ExcelWriter(tmp_file.name, engine='xlsxwriter')
        df.to_excel(excel_writer, sheet_name='Sheet1',
                    index=False, header=False, startrow=1)

        workbook = excel_writer.book
        worksheet = excel_writer.sheets['Sheet1']

        # Define formats
        format_black_bg_white_font = workbook.add_format(
            {'bg_color': '#000000', 'font_color': '#FFFFFF', 'font_size': 14, "border": 1})
        format_pale_yellow_bg_black_font = workbook.add_format(
            {'bg_color': '#FFFF99', 'font_color': '#000000', 'font_size': 14, "border": 1})
        format_baby_blue_bg_black_font = workbook.add_format(
            {'bg_color': '#CCEFFF', 'font_color': '#000000', 'font_size': 14, "border": 1})
        format_pale_orange_bg_black_font = workbook.add_format(
            {'bg_color': '#FFCC99', 'font_color': '#000000', 'font_size': 14, "border": 1})
        format_pale_blue_bg_black_font = workbook.add_format(
            {'bg_color': '#D0E4F5', 'font_color': '#000000', 'font_size': 14, "border": 1})
        format_pale_white_bg_black_font = workbook.add_format(
            {'bg_color': '#F8F8F8', 'font_color': '#000000', 'font_size': 14, "border": 1})

        # Apply formatting to headers and all rows for specific columns
        column_formats = {
            0: format_black_bg_white_font,    # "社員コード"
            1: format_pale_yellow_bg_black_font,  # "社員名"
            2: format_baby_blue_bg_black_font,    # "国籍"
            3: format_pale_orange_bg_black_font,  # "合計労働時間"
            4: format_pale_orange_bg_black_font,  # "夜勤時間"
            # Map other columns as needed
            # get the last two column
            5: format_pale_white_bg_black_font,
            6: format_pale_white_bg_black_font,
            7: format_pale_white_bg_black_font,
            8: format_pale_white_bg_black_font,
            9: format_pale_white_bg_black_font,
            10: format_pale_white_bg_black_font,
            11: format_pale_white_bg_black_font,
            12: format_pale_white_bg_black_font,
            13: format_pale_white_bg_black_font,
            14: format_pale_blue_bg_black_font,
            15: format_pale_blue_bg_black_font
        }

        # Write headers with formatting
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header,
                            column_formats.get(col_num, None))

        # Apply formats to all rows in specified columns
        for col_num, col_format in column_formats.items():
            if col_format:
                # +1 because row indexing starts at 1 and we skip header row
                for row_num in range(1, len(df) + 1):
                    worksheet.write(row_num, col_num,
                                    df.iloc[row_num - 1, col_num], col_format)

        # Adjust column widths based on content
        for col_num, header in enumerate(headers):
            max_len = max(df.iloc[:, col_num].astype(
                str).str.len().max(), len(header))
            # Adjust for padding
            worksheet.set_column(col_num, col_num, max_len + 5)

            # if header is  社員名 make padding to 12
            if col_num == 0:
                worksheet.set_column(col_num, col_num, max_len + 20)

            if col_num == 2:
                worksheet.set_column(col_num, col_num, max_len + 8)

        excel_writer.close()

    response = FileResponse(
        tmp_file.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="salarycalculation.xlsx"
    )
    # Cleanup: Remove the temporary file after sending the response
    # os.unlink(tmp_file.name)
    return response


# ============================= END STAFF SHIFT HTTP ENDPOINT ============================= #

# ============================= END STAFF LEAVE REQUEST HTTP ENDPOINT ============================= #


@router.get("/leave_requests")
async def get_all_leave_requests():
    raw_requests = await Leave_Request.all().prefetch_related('staff').values(
        "id", "start_date", "end_date", "details", "status", "created_at",
        "staff__english_name", "staff__japanese_name", "staff__staff_code"
    )

    # Reform the data to include a nested staff object
    requests = [
        {
            "id": req["id"],
            "start_date": req["start_date"],
            "end_date": req["end_date"],
            "details": req["details"],
            "status": req["status"],
            "created_at": req["created_at"],
            "staff": {
                "english_name": req["staff__english_name"],
                "japanese_name": req["staff__japanese_name"],
                "staff_code": req["staff__staff_code"]
            }
        } for req in raw_requests
    ]

    return requests


@router.get("/leave_requests/{staff_id}")
async def get_staff_leave_requests(staff_id: str):

    # get the staff id by staff_code
    staff = await Staff.get(staff_code=staff_id, leave_date=None).values('id')
    if not staff:
        raise HTTPException(status_code=400, detail="Invalid staff code.")

    # print(staff["id"])

    requests = []
    # mys id/staff code
    if staff_id == "all":
        # get all staff leave_requests
        requests = await Leave_Request.all().values("id", "start_date", "end_date", "details", "status")
    else:
        # fetch by id
        requests = await Leave_Request.filter(staff=staff["id"]).values("id", "start_date", "end_date", "details", "status")

    return requests

    # return {"status": "success", "message": "Successfully imported staff leave requests."}


@router.post('/add_leave_request')
async def create_staff_leave_request(leave_request_json: str = Form(...)):
    leave_request_data = json.loads(leave_request_json)

    staff_mys_id = leave_request_data.pop('mys_id')

    # get the staff id by staff_code
    staff = await Staff.get(staff_code=staff_mys_id, leave_date=None).values('id')

    # add staff_id on leave_request_data
    leave_request_data['staff_id'] = staff['id']

    # check if this existing staff id has pending leave request
    pending_request = await Leave_Request.filter(staff_id=staff['id'], status="pending").first()
    if pending_request:
        raise HTTPException(status_code=400, detail="pending_leave_request")

    leave_request_data["status"] = "pending"

    leave_request = await Leave_Request.create(**leave_request_data)

    # get staff info by id
    staff_info = await Staff.get(id=staff['id']).values('english_name', 'japanese_name', 'staff_code')

    # notification param object
    notification = {
        # "person": leave_request_data['staff']
        "staff": staff_info,
        # "mys_id": leave_request_data['mys_id'],
        "subject": "Leave Request Created",
    }

    # create notifications
    await create_and_broadcast_notification("leaveRequest", json.dumps(notification))

    new_leave_request = await leave_request_pydantic.from_tortoise_orm(leave_request)

    return new_leave_request


@router.put('/update_leave_request')
async def update_staff_leave_request(leave_request_json: str = Form(...)):
    leave_request_data = json.loads(leave_request_json)

    leave_request_id = leave_request_data.pop('id', None)
    leave_request_staff = leave_request_data.pop('staff', None)
    staff_code = leave_request_staff['staff_code']

    if leave_request_id is None:
        raise ValueError("The 'id' field is required.")

    # Update leave request
    await Leave_Request.filter(id=leave_request_id).update(status=leave_request_data['status'])

    # print(staff_code)

    # notification param object
    notification = {
        # "person": leave_request_data['staff']
        # "staff": leave_request_staff,
        # "mys_id": leave_request_data['mys_id'],
        "subject": "Leave Request Updated",
        "status": leave_request_data['status'],
    }

    # # create notifications
    await create_and_broadcast_notification("updateLeaveRequest", json.dumps(notification), recipient=staff_code)

    updated_leave_request = await leave_request_pydantic.from_queryset_single(Leave_Request.get(id=leave_request_id))

    new_leave_request = updated_leave_request.dict()

    new_leave_request["staff"] = leave_request_staff

    return new_leave_request


@router.delete('/delete_leave_request/{id}')
async def delete_staff_leave_request(id: str):
    await Leave_Request.filter(id=id).delete()

    # # notification param object
    # notification = {
    #     # "person": leave_request_data['staff']
    #     "staff": leave_request_staff,
    #     # "mys_id": leave_request_data['mys_id'],
    #     "subject": "Leave Request Updated",
    # }

    # # create notifications
    # await create_and_broadcast_notification("deleteLeaveRequest", json.dumps(notification))

    return id
