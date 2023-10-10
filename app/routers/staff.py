from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

# models
from app.models.user import User
from app.models.staff import Staff, staff_pydantic, staffSelect_pydantic
from app.models.staff_workschedule import Staff_WorkSchedule, staff_workschedule_pydantic

# helpers 
from app.helpers.zipfile import zipfiles
from app.helpers.generate_pdf import fill_pdf_contract
from app.helpers.onedrive import read_from_onedrive, upload_file_to_onedrive

# s3
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url, upload_image_to_s3, is_file_exists

#schema
from app.models.staff_schema import StaffLicense, LicenseData

from tempfile import NamedTemporaryFile

# one drive
# from app.helpers.onedrive import get_access_token
# import httpx

s3_staffimage_upload_folder = 'uploads/staff/img/'

s3_staffbankcard_upload_folder = 'uploads/staff/bank_img/'

s3_license_upload_folder = 'uploads/staff/pdf/'
s3_contracts_folder = 'uploads/staff/contracts/'

router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
    responses={404: {"some_description": "Not found"}}
)

@router.get("")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_staff(staff_group: str):
    # get the user email from the token
    # for more security later, we can use the user id instead of email
    # user_email = verify_token_email(user_email_token)

    # get the user id from the token # change this later to token id
    # user = await User.get(email=user_email_token).values('id')

    # group the list with the staff group "caregiver" or "user"
    # if staff_group == 'staff' or staff_group  == 'スタッフ':
    #     staff = Staff.filter(disabled=False, staff_group='スタッフ',
    #                             # user_id=user_id['id']).order_by('display_order').all()
    #                             user_id=user['id']).all()
    # elif staff_group == 'user' or staff_group == '利用者':
    #     staff = Staff.filter(disabled=False, staff_group='利用者',
    #                             # user_id=user_id['id']).order_by('display_order').all()
    #                             user_id=user['id']).all()

    # get all staff and just filter with staff group
    # if staff_group == 'staff' or staff_group  == 'スタッフ':
    # staff = Staff.filter(disabled=False).order_by('zaishoku_joukyou').all()
    staff = Staff.filter(disabled=False, zaishoku_joukyou__not="退社済").order_by('staff_code').all()
    # elif staff_group == 'user' or staff_group == '利用者':
    #     staff = Staff.filter(disabled=False, staff_group='利用者').all()

    staff_list = await staff_pydantic.from_queryset(staff)

    # convert licenses and bank_card_iamges to json
    # check first if there is licenses or bank_card_images
    for staff in staff_list:
        if staff.licenses is not None:
            staff.licenses = json.loads(staff.licenses)
        if staff.bank_card_images is not None:
            staff.bank_card_images = json.loads(staff.bank_card_images)
        # print(staff.licenses)


    return staff_list

@router.get("/staff_select")
async def get_staff_select():
    
    # same as staff but only take id, english_name, japanese_name, staff_group, duty_type
    staff = Staff.filter(disabled=False).exclude(zaishoku_joukyou="退社済").all()

    staff_list = await staffSelect_pydantic.from_queryset(staff)

    # dont use pydantic

    return staff_list

@router.post("/add_staff")
async def create_staff(staff_json: str = Form(...), staff_image: UploadFile = File(None), licenses: List[UploadFile] = File(None), bank_card_front: UploadFile = File(None), bank_card_back: UploadFile = File(None)):
    staff_data = json.loads(staff_json)

    # file_names = []
    now = datetime.now()
    if licenses is not None:
        for file in licenses:
        # You can access file properties like filename, content type, and content
        # file_names.append(file.filename)

        # create a new filename string with file name plus timestamp
            new_file_name = file.filename.split('.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]
            # upload to s3 bucket
            uploaded_file = upload_file_to_s3(file, new_file_name, s3_license_upload_folder)

            s3_file_path = s3_license_upload_folder + new_file_name
            
            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # the license list has the same length as the staff_data's licenses list please change the value to the new file name in the staff_data
            staff_data['licenses'][licenses.index(file)]['file'] = s3_read_url
            # replace the file object with the s3 url

        staff_data['licenses'] = json.dumps(staff_data['licenses'])
    
    
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

    if bank_card_front or bank_card_back is not None:
        bank_card_front_name = now.strftime("_front_%Y%m%d_%H%M%S") + '.' + bank_card_front.filename.split('.')[-1]
        bank_card_back_name = now.strftime("_back_%Y%m%d_%H%M%S") + '.' + bank_card_back.filename.split('.')[-1]
        
        s3_bankimage_path_front = s3_staffbankcard_upload_folder + bank_card_front_name
        s3_bankimage_path_back = s3_staffbankcard_upload_folder + bank_card_back_name

        uploaded_file_front = upload_image_to_s3(bank_card_front, bank_card_front_name, "bank_img")
        card_front_read_url = generate_s3_url(s3_bankimage_path_front, 'read')

        uploaded_file_back = upload_image_to_s3(bank_card_back, bank_card_back_name, "bank_img")
        card_back_read_url = generate_s3_url(s3_bankimage_path_back, 'read')

        # put this two url in a dictionary like {"front": "url", "back": "url"}
        bank_card_images = {"front": card_front_read_url, "back": card_back_read_url}

        #append
        staff_data['bank_card_images'] = json.dumps(bank_card_images)

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

    # if there is only bank card images added
    if bank_card_back and bank_card_front is not None:
        #convert bank_card_images to json
        new_staff.bank_card_images = json.loads(new_staff.bank_card_images)
    else:
        new_staff.bank_card_images = {}

    return new_staff

@router.put("/update_staff")
async def update_staff(staff_json: str = Form(...), staff_image: UploadFile = File(None), licenses: List[UploadFile] = File(None),  bank_card_front: UploadFile = File(None), bank_card_back: UploadFile = File(None)):
    staff_data = json.loads(staff_json)

    now = datetime.now()
    if licenses is not None:
        for file in licenses:
        # You can access file properties like filename, content type, and content
        # file_names.append(file.filename)

        # create a new filename string with file name plus timestamp
            new_file_name = file.filename.split('.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]
            # upload to s3 bucket
            uploaded_file = upload_file_to_s3(file, new_file_name, s3_license_upload_folder)

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

    if bank_card_front or bank_card_back is not None:
        bank_card_front_name = now.strftime("_front_%Y%m%d_%H%M%S") + '.' + bank_card_front.filename.split('.')[-1]
        bank_card_back_name = now.strftime("_back_%Y%m%d_%H%M%S") + '.' + bank_card_back.filename.split('.')[-1]
        
        s3_bankimage_path_front = s3_staffbankcard_upload_folder + bank_card_front_name
        s3_bankimage_path_back = s3_staffbankcard_upload_folder + bank_card_back_name

        uploaded_file_front = upload_image_to_s3(bank_card_front, bank_card_front_name, "bank_img")
        card_front_read_url = generate_s3_url(s3_bankimage_path_front, 'read')

        uploaded_file_back = upload_image_to_s3(bank_card_back, bank_card_back_name, "bank_img")
        card_back_read_url = generate_s3_url(s3_bankimage_path_back, 'read')

        # put this two url in a dictionary like {"front": "url", "back": "url"}
        bank_card_images = {"front": card_front_read_url, "back": card_back_read_url}

        #append
        staff_data['bank_card_images'] = json.dumps(bank_card_images)

    staff_data_copy = staff_data.copy()
    
    staff_data_copy.pop('id')

    # update staff
    await Staff.filter(id=staff_data['id']).update(**staff_data_copy)
    

    updated_staff = await staff_pydantic.from_queryset_single(Staff.get(id=staff_data['id']))

    # if there is only license
    if licenses is not None:
    # convert licenses to json
        updated_staff.licenses = json.loads(updated_staff.licenses)
    else:
        updated_staff.licenses = []

     # if there is only bank card images added
    if bank_card_back and bank_card_front is not None:
        #convert bank_card_images to json
        updated_staff.bank_card_images = json.loads(updated_staff.bank_card_images)
    else:
        updated_staff.bank_card_images = {}

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

# for csv
# @router.get('/download')
# async def download_staff_list():
#     # get all staff which is ordered by  zaishoku_joukyou
#     staff = await Staff.filter(disabled=False).order_by('staff_code','zaishoku_joukyou').values('affiliation', 'staff_code', 'english_name', 'japanese_name', 'nationality', 'join_date',
#                                                                                     'leave_date', 'postal_code', 'prefecture', 'municipality', 'town',
#                                                                                     'building', 'phone_number', 'email', 'koyou_keitai', 'zaishoku_joukyou',)

#     df = pd.DataFrame(staff)

#     headers = ["所属", "社員番号", "NAME", "職員名", "国籍 ", "入社年月日", "退社年月日", "郵便番号",
#                 "都道府県", "市区町村", "町名以下", "建物名", "職員電話番号", "職員Eメールアドレス", "雇用形態", "在職状況"]

#     csv_str = df.to_csv(index=False, header=headers)

#     # Set response headers for CSV download
#     response = Response(content=csv_str, media_type="text/csv; charset=utf-8")
#     response.headers["Content-Disposition"] = "attachment; filename=staff.csv"

#     return response

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
        worksheet = excel_writer.sheets['Sheet1']  # You may need to adjust the sheet name

        # Adjust column widths based on content
        # for i, col in enumerate(headers):
        #     column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)  # +2 for padding
        #     worksheet.set_column(i, i, column_len)

        # Adjust column widths based on content
        for i in range(len(headers)):
            max_len = df.iloc[:, i].astype(str).str.len().max()
            column_len = max(max_len, len(headers[i]) + 2)  # +2 for padding
            worksheet.set_column(i, i, column_len)

        #FFD580
        format_orange = workbook.add_format({'bg_color': '#FFD580'})  # Red background
        worksheet.conditional_format(
            1,  # Starting row (assuming header is in row 1)
            headers.index('在職状況'),  # Column index of '雇用形態'
            df.shape[0],  # Number of rows
            headers.index('在職状況'),  # Column index of '雇用形態'
            {'type': 'text', 'criteria': 'containing', 'value': '退社済', 'format': format_orange}
        )

        excel_writer.close()  # Close the ExcelWriter to save the Excel file

    # Return the Excel file as a response
    response = FileResponse(tmp_file.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=staff.xlsx"

    return response

# Define a function to apply row coloring
def highlight_rows(row):
    if row["zaishoku_joukyou"] == "退社済":
        return ['background-color: gray'] * len(row)
    else:
        return [''] * len(row)
    


@router.get("/workschedule_list")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_all_schedule():
        # add staffs japanese name and english name in the values
   return await Staff_WorkSchedule.all().values()


@router.post('/add_workschedule')
async def create_workschedule(staff_workschedule_json: str = Form(...)):
    work_schedule_data = json.loads(staff_workschedule_json)

    staff_data = work_schedule_data.pop('staff')
    #get id from staff_data 
    staff_id = staff_data['id']

    # add staff_id on work_schedule_data
    work_schedule_data['staff_id'] = staff_id

    print(work_schedule_data)

    schedule = await Staff_WorkSchedule.create(**work_schedule_data)

    new_schedule = await staff_workschedule_pydantic.from_tortoise_orm(schedule)

    return new_schedule