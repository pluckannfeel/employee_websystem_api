from datetime import datetime
import shutil
import os
import json
import time
import requests
import base64
import jwt
import datetime

from typing import List, Type
import uuid
from dotenv import load_dotenv

# helpers, libraries
from typing import List, Type
from dotenv import load_dotenv
from app.helpers.definitions import get_directory_path
from app.helpers.s3_file_upload import upload_image_to_s3
from app.helpers.generate_pdf import fill_pdf_sputum_training, fill_pdf_contract, fill_pdf_pledge

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

        return generated_document[0]

    elif (details['document_name'] == 'mys_contract'):
        generated_document = fill_pdf_contract(details['staff'])

        return generated_document[0]
    elif (details['document_name'] == 'mys_pledge'):

        generated_document = fill_pdf_pledge(details['staff'])

        # await send_for_signature(details['staff'], generated_document[0])

        return generated_document[0]
    else:
        raise HTTPException(status_code=400, detail="Invalid document name")


# def get_docusign_access_token(client_id, client_secret, authorization_code, redirect_uri, base_url):
#     token_url = f"{base_url}/oauth/token"

#     data = {
#         'code': authorization_code,
#         'grant_type': 'authorization_code',
#         'client_id': client_id,
#         'client_secret': client_secret,
#         'redirect_uri': redirect_uri
#     }

#     response = requests.post(token_url, data=data)

#     if response.status_code == 200:
#         token_data = response.json()
#         access_token = token_data['access_token']
#         refresh_token = token_data['refresh_token']
#         expires_in = token_data['expires_in']
#         return access_token, refresh_token, expires_in
#     else:
#         raise Exception("Failed to obtain access token")


# def refresh_docusign_access_token(client_id, client_secret, refresh_token, base_url):
#     token_url = f"{base_url}/oauth/token"

#     data = {
#         'refresh_token': refresh_token,
#         'grant_type': 'refresh_token',
#         'client_id': client_id,
#         'client_secret': client_secret
#     }

#     response = requests.post(token_url, data=data)

#     if response.status_code == 200:
#         token_data = response.json()
#         access_token = token_data['access_token']
#         expires_in = token_data['expires_in']
#         return access_token, expires_in
#     else:
#         raise Exception("Failed to refresh access token")

# def get_docusign_access_token(jwt_token):
#     token_url = 'https://account-d.docusign.com/oauth/token'

#     headers = {
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }

#     payload = {
#         'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
#         'assertion': jwt_token
#     }

#     response = requests.post(token_url, headers=headers, data=payload)

#     if response.status_code == 200:
#         token_data = response.json()
#         access_token = token_data['access_token']
#         print(access_token)
#         expires_in = token_data['expires_in']

#         return access_token, expires_in
#         # Use the obtained access token for API requests
#     else:
#         raise Exception("Failed to obtain access token")


# async def send_for_signature(recipient, document_url):
#     docusign_base_url = 'https://demo.docusign.net/restapi/v2'
#     docusign_account_id = '7cde6d5b-4f3a-44b8-a50f-583e9f5ae80a'
#     # docusign_access_token = 'https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature&client_id=cccfc420-75b5-4abf-b5b1-b17b76d4b3ef&redirect_uri=http://localhost:3000/admin/'

#     recipient_email = recipient["personal_email"] if recipient["personal_email"] else recipient["work_email"]

#     if recipient_email is None:
#         return False
#     else:
#         integration_key = 'cccfc420-75b5-4abf-b5b1-b17b76d4b3ef'
#         private_key_file = 'path/to/your/private-key.pem'

#         # token_data = {
#         #     'authorization_code': 'eyJ0eXAiOiJNVCIsImFsZyI6IlJTMjU2Iiwia2lkIjoiNjgxODVmZjEtNGU1MS00Y2U5LWFmMWMtNjg5ODEyMjAzMzE3In0.AQoAAAABAAYABwCA-eOdq_vbSAgAgIVq5av720gCABEHU0v4zCFFr0-gxLoGWb0VAAEAAAAYAAEAAAAFAAAADQAkAAAAY2NjZmM0MjAtNzViNS00YWJmLWI1YjEtYjE3Yjc2ZDRiM2VmIgAkAAAAY2NjZmM0MjAtNzViNS00YWJmLWI1YjEtYjE3Yjc2ZDRiM2VmNwBdcJVqPFzDRI6_go1WcO97MAAAqjnyqPvbSA.14VCJJt0BARzVOTABou6tNM4X0dL9PVRkI5sG0gm9BmH8PELQR_pMDzwvp4InWHg9Hkp-8T7YBoyWFhjWXU4qTCDDT8EuyNtgFabtfi9-8EtMilyxfjTFMiQEVxmlejZe_1SfAtOF8bOVphJbgcj0InWu-PkeHogjDQxNtoaeiUAkMYgJIZnFtXqmmeqTi7WSjKUOea6dfmlG5CWH3OKOsnHbvqr7JMFawVU5Ov7Q1T8kzT3MUc_yXzxtS2RW2YF58M6bUieKEeaDlGmF4VBQeb00D5frWqRnvcUFY8wJlPbyHUpUzMnJjmwfIhoSB6bKt0ytkbv3fiJmhveBb6hig',
#         #     'grant_type': 'authorization_code',
#         #     'client_id': 'cccfc420-75b5-4abf-b5b1-b17b76d4b3ef',
#         #     'client_secret': '387f12f3-1dd7-40b8-802e-8543dfdce91f',
#         #     'redirect_uri': 'http://localhost:8000/'
#         # }

#         # access_token, refresh_token, expires_in = get_docusign_access_token(token_data['client_id'], token_data['client_secret'], token_data['authorization_code'], token_data['redirect_uri'],docusign_base_url)

#         # # Use the access token for DocuSign API requests

#         # # Check if the access token is expired
#         # if expires_in <= 0:
#         #     # Refresh the access token
#         #     access_token, expires_in = refresh_docusign_access_token(token_data['client_id'], token_data['client_secret'], refresh_token, docusign_base_url)

#         # Path to the private key file in the root directory
#         private_key_file = 'privatekey.pem'

#         # Create a JWT token
#         payload = {
#             'iss': integration_key,
#             'sub': integration_key,
#             'aud': 'account-d.docusign.com',
#             'iat': datetime.datetime.utcnow(),
#             'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
#         }

#         with open(private_key_file, 'rb') as private_key:
#             private_key_contents = private_key.read()
#             # print(private_key_contents)
#             jwt_token = jwt.encode(
#                 payload, private_key_contents, algorithm='RS256')

#             access_token, expires_in = get_docusign_access_token(jwt_token)

#             if (access_token):
#                 document_response = requests.get(document_url)

#                 if document_response.status_code == 200:

#                     base64_document = base64.b64encode(
#                         document_response.content).decode('utf-8')

#                     # envolope
#                     envelope = {
#                         "documents": [
#                             {
#                                 "documentBase64": base64_document,
#                                 "documentId": "1",
#                                 "fileExtension": "pdf",
#                                 # "name": "sample"
#                             }
#                         ],
#                         "recipients": {
#                             "signers": [
#                                 {
#                                     "email": recipient_email,
#                                     "name": recipient["english_name"],
#                                     "recipientId": "1",
#                                     "routingOrder": "1",
#                                     # "tabs": {
#                                     #     "signHereTabs": [
#                                     #         {
#                                     #             "anchorString": "signHere:",
#                                     #             "anchorUnits": "pixels",
#                                     #             "anchorXOffset": "20",
#                                     #             "anchorYOffset": "10"
#                                     #         }
#                                     #     ]
#                                     # }
#                                 }
#                             ]
#                         }
#                     }

#                     response = requests.post(f"{docusign_base_url}/accounts/{docusign_account_id}/envelopes", json=envelope, headers={
#                         "Authorization": f"Bearer {access_token}",
#                         "Content-Type": "application/json"
#                     })

#                     print("docusign email sent", response.json())

#                 else:
#                     raise HTTPException(
#                         status_code=500, detail="Failed to fetch the document from S3")
