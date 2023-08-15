from ctypes import Union
import email
import json
import os
from typing import Type
from unicodedata import name
from passlib.context import CryptContext
import jwt
from dotenv import dotenv_values

# FastAPI
from fastapi import HTTPException, status
from tortoise.expressions import Q

# models
from app.models.user import User

# helper
from app.helpers.user import UUIDEncoder, UUIDDecoder

# config_credentials
# env_credentials = dotenv_values('.env')
secret_key = os.environ['SECRET_KEY']

# password hash context
password_hash_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return password_hash_context.hash(password)


def verify_password(input_password: str, hashed_password: str) -> str:
    return password_hash_context.verify(input_password, hashed_password)


async def get_user_credentials(token: str):
    try:
        payload = jwt.decode(
            token, secret_key, algorithms="HS256")
        user = await User.get(id=payload.get("id"))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def verify_token_email(token: str):
    try:
        payload = jwt.decode(
            token, secret_key, algorithms="HS256")
        print("UUID: " + json.loads(payload.get("id")))
        user_id = json.loads(payload.get("id"))
        user = await User.get(id=user_id)
        print(f"user: {user}")
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def verify_password(input_password, hashed_password):
    return password_hash_context.verify(input_password, hashed_password)


async def authenticate_user(username_or_email: str, input_password: str):
    # user = await User.get(Q(username=username_or_email) | Q(email=username_or_email))
    user = await User.get(email=username_or_email)
    # print(user.password_hash)
    is_authenticated = password_hash_context.verify(
        input_password, user.password_hash)
    if user:
        if is_authenticated:
            return user

    return False


# password is actually password_hash in models
async def token_generator(email: str, password: str) -> str:
    user = await authenticate_user(email, password)
    # print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            # headers={"WWW-Authenticate": "Basic"},
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = {
        "id": json.dumps(user.id, separators=('-', '_'), cls=UUIDEncoder),
        "email": user.email
    }
    print(token_data)

    token = jwt.encode(token_data, secret_key, algorithm="HS256")

    return token


if __name__ == '__main__':
    authenticate_user('admin', 'admin')
