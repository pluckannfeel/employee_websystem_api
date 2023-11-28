from datetime import datetime
import shutil
import os
import json
import time

from typing import List, Type
import uuid
from dotenv import load_dotenv

# helpers, libraries
from typing import List, Type
from dotenv import load_dotenv
from app.helpers.definitions import get_directory_path
from app.helpers.s3_file_upload import upload_image_to_s3
from app.helpers.generate_pdf import fill_pdf_sputum_training, fill_pdf_contract

from tortoise.contrib.fastapi import HTTPNotFoundError

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, Form, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse


from app.models.company import Company, company_pydantic


documents_upload_path = 'uploads/companies/documents/'


router = APIRouter(
    prefix="/companies",
    tags=["Company"],
    responses={404: {"some_description": "Not found"}}
)

load_dotenv()


def is_valid_uuid(input_string):
    try:
        uuid_obj = uuid.UUID(input_string)
        return True
    except ValueError:
        return False


@router.get("")
async def get_companies():
    companies = await Company.all().values()
    return companies

# get company info by organization_code or id


@router.get("/{company_id}")
async def get_company(company_id: str):
    if is_valid_uuid(company_id):
        company = await Company.get(id=company_id).values()
    else:
        company = await Company.get(organization_code=company_id).values()
    return company


@router.put("/update_company")
async def update_company(company_json: str = Form(...)):
    company_data = json.loads(company_json)

    data_copy = company_data.copy()

    data_copy.pop('id')

    await Company.get(id=company_data['id']).update(**data_copy)

    updated_company = await company_pydantic.from_queryset_single(Company.get(id=company_data['id']))

    return updated_company


@router.post("/generate_document")
async def generate_document(details: str = Form(...)):
    details = json.loads(details)

    # check if details has None values, if there is raise an error
    if any(value is None for value in details.values()):
        raise HTTPException(status_code=400, detail="Invalid details")

    # generation of document differs with document name, so we have to check the document name
    if (details['document_name'] == 'docs_sputum_training'):
        # there are functions per document type in generate_pdf.py
        # print("here")
        generated_document = fill_pdf_sputum_training(
            details['staff'], details['patient'], details['institution'], details['date_created'])
        
    elif (details['document_name'] == 'mys_contract'):
        generated_document = fill_pdf_contract(details['staff'])


        return generated_document[0]
    else:
        raise HTTPException(status_code=400, detail="Invalid document name")
