from datetime import datetime
import shutil
import os
import time

from typing import List, Type
from dotenv import load_dotenv

# helpers, libraries
from typing import List, Type
from dotenv import load_dotenv
from app.helpers.definitions import get_directory_path
from app.helpers.s3_file_upload import upload_image_to_s3
from app.helpers.data_checker import DataChecker as data_checker

# tortoise
from tortoise.contrib.fastapi import HTTPNotFoundError

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# models
from app.models.user import User, user_pydantic
from app.models.user_schema import CreateUser, CreateUserToken, ChangeUserPassword, UpdateUserInfo

# authentication
from app.auth.authentication import hash_password, token_generator, verify_password, verify_token_email

# email user verification
from app.auth.email_verification import send_email

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    # dependencies=[Depends(e.g get_token_header)] # from dependencies.py
    # responses={404: {"some_description": "Not found"}}
)  # if you put args here this will be pass to all funcs below you can override it by adding it directly to each

load_dotenv()
# file upload local
upload_path = get_directory_path() + '\\uploads'
# file upload s3 bucket
s3_upload_path = str(os.getenv("AWS_PPS_STORAGE_URI")) + 'uploads'


@router.get("/", response_model=List[user_pydantic])
async def get_users():
    return await user_pydantic.from_queryset(User.all())


@router.get("/{email}", tags=["Users"], name="Get user by email", response_model=user_pydantic, responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def read_user(email: str):
    return await user_pydantic.from_queryset_single(User.get(email=email))


@router.get("/verification/", tags=["Users"], name="Verify User", responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def verify_user(token: str):  # request: Request,
    user = await verify_token_email(token)
    print("user object ", user)
    if user:
        if not user.is_verified:
            user.is_verified = True
            # await User.filter(id=user.id).update()
            await user.save()
            return {"msg": "user successfully verified."}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired token.",
        headers={"WWW-Authenticate": "Bearer"}
    )


@router.post("/register", tags=["Users"], status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUser) -> dict:
    # if you use user_pydantic_
    # user: userIn_pydantic
    # user_info = user.dict(exclude_unset=True)

    # note: not a good idea to put validations here, e.g for password: password is hashed after this line, its better to check the password field in front end

    user_info = user.dict(exclude_unset=True)

    # check if email already exists
    if await User.filter(email=user_info['email']).exists():
        raise HTTPException(
            status_code=401,
            detail="Email already exists.",
            headers={'WWW-Authenticate": "Bearer'}
        )

    user_data = await User.create(
        first_name=user_info['first_name'], last_name=user_info['last_name'],
        #   birth_date=user_info['birth_date'],
        #   username=user_info['username'],
        email=user_info['email'],
        # phone=user_info['phone'],
        role=user_info['role'],
        password_hash=hash_password(user_info['password'].get_secret_value()))
    # user_obj = await User.create(**user_info)

    new_user = await user_pydantic.from_tortoise_orm(user_data)

    emails = [new_user.email]

    # if new_user:
    #     print("New user: " + new_user.email)
    #     # for sending email verification
    #     await send_email(emails, new_user)

    return {'user': new_user, 'msg': "new user created."}


@router.get("/check_user_info/", tags=["Users"], status_code=status.HTTP_200_OK)
async def check_user_credentials(token: str) -> dict:
    # key - token
    user = await verify_token_email(token)
    print("user object ", user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # the_user = await User.get(email=email).values('id')

    user_data = object()

    # add this for future purposes if you want to add user image
    # this include the user_img table
    joined_data = False
    # joined_data = await User_Img.filter(user=the_user['id']).prefetch_related('user').order_by('-created_at').values('img_url', 'user__username', 'user__first_name', 'user__last_name', 'user__birth_date', 'user__email', 'user__phone', 'user__is_verified', 'user__created_at')

    # SQL = User_Img.filter(user=the_user['id']).prefetch_related('user').values('img_url', 'user__username', 'user__first_name', 'user__last_name', 'user__birth_date', 'user__email', 'user__phone', 'user__is_verified', 'user__created_at').sql()
    # print(SQL)

    # if joined data is empty return data without user_img table
    # removed birthdate and username
    # if not joined_data:
    user_only_data = await User.filter(email=user.email).values('id', 'first_name', 'last_name', 'email', 'phone', 'job', 'role', 'created_at')
    print(user_only_data[0]['email'])

    # transform
    user_data = {
        # 'username': joined_data[0]['user__username'] if joined_data else user_only_data[0]['username'],
        'id': joined_data[0]['user__id'] if joined_data else user_only_data[0]['id'],
        'firstName': joined_data[0]['user__first_name'] if joined_data else user_only_data[0]['first_name'],
        'lastName': joined_data[0]['user__last_name'] if joined_data else user_only_data[0]['last_name'],
        'email': joined_data[0]['user__email'] if joined_data else user_only_data[0]['email'],
        'phone': joined_data[0]['user__phone'] if joined_data else user_only_data[0]['phone'],
        'job': joined_data[0]['user__job'] if joined_data else user_only_data[0]['job'],
        # 'birth_date': joined_data[0]['user__birth_date'] if joined_data else user_only_data[0]['birth_date'],
        # 'is_verified': joined_data[0]['user__is_verified'] if joined_data else user_only_data[0]['is_verified'],
        'role': joined_data[0]['user__role'] if joined_data else user_only_data[0]['role'],
        'created_at': joined_data[0]['user__created_at'] if joined_data else user_only_data[0]['created_at'],
        'img_url': joined_data[0]['img_url'] if joined_data else ''
    }

    return user_data


@router.get("/get_user_info/", tags=["Users"], status_code=status.HTTP_200_OK)
async def get_user_credentials(email: str) -> dict:
    user = await User.get(email=email).values('id')

    user_data = object()

    # add this for future purposes if you want to add user image
    # this include the user_img table
    joined_data = False
    # joined_data = await User_Img.filter(user=the_user['id']).prefetch_related('user').order_by('-created_at').values('img_url', 'user__username', 'user__first_name', 'user__last_name', 'user__birth_date', 'user__email', 'user__phone', 'user__is_verified', 'user__created_at')

    # SQL = User_Img.filter(user=the_user['id']).prefetch_related('user').values('img_url', 'user__username', 'user__first_name', 'user__last_name', 'user__birth_date', 'user__email', 'user__phone', 'user__is_verified', 'user__created_at').sql()
    # print(SQL)

    # if joined data is empty return data without user_img table
    # removed birthdate and username
    # if not joined_data:
    user_only_data = await User.filter(id=user['id']).values('id', 'first_name', 'last_name', 'email', 'phone', 'job', 'role', 'created_at', 'is_verified')
    print(user_only_data[0]['email'])

    # transform
    user_data = {
        # 'username': joined_data[0]['user__username'] if joined_data else user_only_data[0]['username'],
        'id': joined_data[0]['user__id'] if joined_data else user_only_data[0]['id'],
        'firstName': joined_data[0]['user__first_name'] if joined_data else user_only_data[0]['first_name'],
        'lastName': joined_data[0]['user__last_name'] if joined_data else user_only_data[0]['last_name'],
        'email': joined_data[0]['user__email'] if joined_data else user_only_data[0]['email'],
        'phone': joined_data[0]['user__phone'] if joined_data else user_only_data[0]['phone'],
        'job': joined_data[0]['user__job'] if joined_data else user_only_data[0]['job'],
        # 'birth_date': joined_data[0]['user__birth_date'] if joined_data else user_only_data[0]['birth_date'],
        # 'is_verified': joined_data[0]['user__is_verified'] if joined_data else user_only_data[0]['is_verified'],
        'role': joined_data[0]['user__role'] if joined_data else user_only_data[0]['role'],
        'is_verified': joined_data[0]['user__is_verified'] if joined_data else user_only_data[0]['is_verified'],
        'created_at': joined_data[0]['user__created_at'] if joined_data else user_only_data[0]['created_at'],
        'img_url': joined_data[0]['img_url'] if joined_data else ''
    }

    return user_data


@router.post("/login", tags=["Users"], status_code=status.HTTP_200_OK)
async def login_user(login_info: CreateUserToken) -> dict:
    token = await token_generator(login_info.email, login_info.password)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={'WWW-Authenticate": "Bearer'}
        )

    return {'token': token, 'email': login_info.email, 'msg': "user logged in."}

# update user info


@router.put('/update_user_info', status_code=status.HTTP_200_OK, tags=["Users"])
async def update_user(user_id: str, user: UpdateUserInfo):

    user_data = user.dict(exclude_unset=True)

    # get user email from id
    user_email = await User.get(id=user_id).values('email')

    # check if the current user is the same as the email entered
    if user_data['email'] == user_email:
        # if user email input matched with the current user email
        # update User without email
        await User.filter(id=user_id).update(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=user_data['phone'],
            job=user_data['job'],
            role=user_data['role']
        )
    else:
        await User.filter(id=user_id).update(**user_data)

    # get the new updated user info
    updated_user_info = await User.get(id=user_id).values('id', 'first_name', 'last_name', 'email', 'phone', 'job', 'role', 'created_at')

    return updated_user_info


@router.put("/change_password", tags=["Users"], status_code=status.HTTP_200_OK)
async def change_user_password(user_info: ChangeUserPassword) -> dict:
    user = await User.get(email=user_info.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    old_password = user_info.old_password.get_secret_value()

    if not await verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user.password_hash = hash_password(
        user_info.new_password.get_secret_value())
    await user.save()

    return {'msg': "Password successfully changed."}

# @router.post("/user_add_img", tags=["Users"], status_code=status.HTTP_201_CREATED)
# # async def add_user_img(user: str, file: UploadFile = File(...)) -> dict:
# async def add_user_img(user: str, file: UploadFile = File(...)):
#     # current path to save on local uploads folder but we will save it on s3 bucket later on
#     # print(user)
#     # print(file.filename)

#     # img_info = user_img.dict()
#     the_user = await User.get(username=user).values('id')
#     username = user

#     # to avoid file name duplicates, lets concatenate datetime and user's name
#     now = datetime.now()
#     new_image_name = username.split('@')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]

#     s3_upload_file = s3_upload_path + '/img/' + new_image_name
#     # check if content type is image
#     is_file_img = file.content_type.startswith('image')

#     # upload image to s3 bucket
#     upload_image_to_s3(file, new_image_name)

#     user_img_data = await User_Img.create(user_id=the_user['id'], img_url=s3_upload_file)

#     new_user_img = await user_img_pydantic.from_tortoise_orm(user_img_data)

#     copied_user = new_user_img.dict(exclude_unset=True).copy()

#     # print('user_data: ', new_user_img)

#     if not new_user_img and not is_file_img:
#         return {'error_msg': "user image not added."}

#     # upload_file = upload_path + '\\' + new_image_name
#     # image_name = image.split('\\')[-1]

#     # save to local directory
#     # with open(upload_file, "wb") as buffer:
#     #     shutil.copyfileobj(file.file, buffer)
#     # time.sleep(2)
#     # after inserting renaem the file
#     # os.rename(upload_file, upload_path + '\\' + new_image_name)

#     img_url = copied_user["img_url"]
#     print(img_url)

#     return {'new_file': file.filename, 'new_img_url': img_url, 'msg': "new user image created."}
