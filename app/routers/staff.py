from datetime import datetime, timedelta
import json

from typing import List, Type

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile

# models
from app.models.user import User
from app.models.staff import Staff, staff_pydantic

# s3
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url, upload_image_to_s3

#schema
from app.models.staff_schema import StaffLicense, LicenseData


s3_upload_folder = 'uploads/staff/img/'

s3_license_upload_folder = 'uploads/staff/pdf/'

router = APIRouter(
    prefix="/staff",
    tags=["Staff"],
    responses={404: {"some_description": "Not found"}}
)

@router.get("/", responses={status.HTTP_201_CREATED: {"model": staff_pydantic}})
async def get_staff(user_email_token: str, staff_group: str):
    # get the user email from the token
    # for more security later, we can use the user id instead of email
    # user_email = verify_token_email(user_email_token)

    # get the user id from the token # change this later to token id
    user = await User.get(email=user_email_token).values('id')

    # group the list with the staff group "caregiver" or "user"
    if staff_group == 'staff' or staff_group  == 'スタッフ':
        staff = Staff.filter(disabled=False, staff_group='スタッフ',
                                # user_id=user_id['id']).order_by('display_order').all()
                                user_id=user['id']).all()
    elif staff_group == 'user' or staff_group == '利用者':
        staff = Staff.filter(disabled=False, staff_group='利用者',
                                # user_id=user_id['id']).order_by('display_order').all()
                                user_id=user['id']).all()

    staff_list = await staff_pydantic.from_queryset(staff)

    # convert licenses to json
    for staff in staff_list:
        staff.licenses = json.loads(staff.licenses)
        print(staff.licenses)


    return staff_list

@router.post("/add_staff", status_code=status.HTTP_201_CREATED)
async def create_staff(staff_json: str = Form(...), staff_image: UploadFile = File(...), licenses: List[UploadFile] = File(None)):
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
            uploaded_file = upload_file_to_s3(file, new_file_name)

            s3_file_path = s3_license_upload_folder + new_file_name
            
            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # the license list has the same length as the staff_data's licenses list please change the value to the new file name in the staff_data
            staff_data['licenses'][licenses.index(file)]['file'] = s3_read_url
            # replace the file object with the s3 url

    # print(staff_data['licenses'])
    # convert licenses to json
    staff_data['licenses'] = json.dumps(staff_data['licenses'])
    

    is_file_image = staff_image.content_type.startswith('image/')

    if not is_file_image:
        raise HTTPException(status_code=400, detail='File uploaded is not an image')
    
    
    image_name = staff_data['english_name'].split(
        ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + staff_image.filename.split('.')[-1]
    
    # s3_img_url = s3_upload_path + image_name
    s3_img_path = s3_upload_folder + image_name

    # upload to s3 bucket
    uploaded_file = upload_image_to_s3(staff_image, image_name)

    print("uploaded: ", uploaded_file)

    s3_read_url = generate_s3_url(s3_img_path, 'read')

    # append s3_read_url to employee_data
    staff_data['img_url'] = s3_read_url

    print("s3_read_url: ", s3_read_url)

    # user = await User.get(id=employee_data['user_id']).values('id')

    # create staff
    staff = await Staff.create(**staff_data)

    new_staff = await staff_pydantic.from_tortoise_orm(staff)
    # new_staff = await Staff.get(id=staff.id).values()

    # convert licenses to json
    new_staff.licenses = json.loads(new_staff.licenses)

    return new_staff

    # return {}


# @router.post("/add_staff", status_code=status.HTTP_201_CREATED)
# async def create_staff(staff_json: str = Form(...), staff_image: UploadFile = File(...), licenses: List[UploadFile] = File(...)):
#     staff_data = json.loads(staff_json)

#     print(staff_data)

#     licenses_data = licenses.licenses

#     for license in licenses_data:
#         print(license.file)

#     # print(licenses)

#     return {}

    # is_file_image = staff_image.content_type.startswith('image/')

    # if not is_file_image:
    #     raise HTTPException(status_code=400, detail='File uploaded is not an image')
    
    # now = datetime.now()
    # image_name = staff_data['english_name'].split(
    #     ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + staff_image.filename.split('.')[-1]
    
    # # s3_img_url = s3_upload_path + image_name
    # s3_img_path = s3_upload_folder + image_name

    # # upload to s3 bucket
    # uploaded_file = upload_image_to_s3(staff_image, image_name)

    # print("uploaded: ", uploaded_file)

    # s3_read_url = generate_s3_url(s3_img_path, 'read')

    # # append s3_read_url to employee_data
    # staff_data['img_url'] = s3_read_url

    # print("s3_read_url: ", s3_read_url)

    # # user = await User.get(id=employee_data['user_id']).values('id')

    # # create staff
    # staff = await Staff.create(**staff_data)

    # new_staff = await staff_pydantic.from_tortoise_orm(staff)

    # return new_staff

@router.put("/update_staff", status_code=status.HTTP_201_CREATED)
async def update_staff(staff_json: str = Form(...), staff_image: UploadFile = File(None), licenses: List[StaffLicense] = Form(...) ):
    staff_data = json.loads(staff_json)

    print(staff_data)

    print(licenses)
    # check if there is an image file
    # if staff_image is not None:
    #     is_file_image = staff_image.content_type.startswith('image/')

    #     if not is_file_image:
    #         raise HTTPException(status_code=400, detail='File uploaded is not an image')
        
    #     now = datetime.now()
    #     image_name = staff_data['english_name'].split(
    #         ' ')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + staff_image.filename.split('.')[-1]
        
    #     # s3_img_url = s3_upload_path + image_name
    #     s3_img_path = s3_upload_folder + image_name

    #     # upload to s3 bucket
    #     uploaded_file = upload_image_to_s3(staff_image, image_name)

    #     print("uploaded: ", uploaded_file)

    #     s3_read_url = generate_s3_url(s3_img_path, 'read')

    #     # append s3_read_url to employee_data
    #     staff_data['img_url'] = s3_read_url

    #     print("s3_read_url: ", s3_read_url)

    # staff_data_copy = staff_data.copy()
    
    # staff_data_copy.pop('id')

    # # update staff
    # await Staff.filter(id=staff_data['id']).update(**staff_data_copy)

    # updated_staff = await staff_pydantic.from_queryset_single(Staff.get(id=staff_data['id']))

    # return updated_staff