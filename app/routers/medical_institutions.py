from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.medical_institution import MedicalInstitution, medical_institution_pydantic
from app.models.user import User

from tempfile import NamedTemporaryFile

router = APIRouter(
    prefix="/medical_institutions",
    tags=["Medical Institution"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("")
async def get_medical_institutions():
    # get all institutions
    medical_institutions = await MedicalInstitution.filter(data_disabled=False).all().values()

    return medical_institutions


@router.post("/add_medical_institution")
async def add_medical_institution(institution_json: str = Form(...)):
    data = json.loads(institution_json)

    now = datetime.now()

    # create new medical institution
    institution = await MedicalInstitution.create(**data)

    new_institution = await medical_institution_pydantic.from_tortoise_orm(institution)

    return new_institution


@router.put("/update_medical_institution")
async def update_medical_institution(institution_json: str = Form(...)):
    data = json.loads(institution_json)

    data_copy = data.copy()

    data_copy.pop('id')

    await MedicalInstitution.filter(id=data['id']).update(**data_copy)

    updated_institution = await MedicalInstitution.get(id=data['id']).values()

    return updated_institution


@router.put("/delete_medical_institutions")
async def delete_medical_institution(institution_json: str = Form(...)):
    data = json.loads(institution_json)

    await MedicalInstitution.filter(id__in=data["institutions"]).update(data_disabled=True)
    
    return data["institutions"]
