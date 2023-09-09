from datetime import date
from typing import List
from pydantic import BaseModel
from fastapi import UploadFile

class StaffLicense(BaseModel):
    number: str
    name: str
    date: date
    file: bytes

class LicenseData(BaseModel):
    licenses: List[StaffLicense]