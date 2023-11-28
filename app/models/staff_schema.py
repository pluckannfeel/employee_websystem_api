from datetime import date
from typing import List
from pydantic import BaseModel, root_validator
from fastapi import UploadFile


class StaffLicense(BaseModel):
    number: str
    name: str
    date: date
    file: bytes


class LicenseData(BaseModel):
    licenses: List[StaffLicense]


class StaffLoginCredentials(BaseModel):
    staff_code: str
    password: str

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        # username, password = values.get('username'), values.get('password')
        # if not password_hash_context.verify(username, password):
        #     raise ValueError('Username and/or password is invalid.')

        return values
