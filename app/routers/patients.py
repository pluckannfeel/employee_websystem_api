from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

# models
from app.models.user import User
from app.models.patient import Patient, patient_pydantic, patientSelect_pydantic

from tempfile import NamedTemporaryFile


s3_patients_upload_img_folder = 'uploads/patients/img/'
s3_patients_upload_pdf_folder = 'uploads/patients/pdf/'

router = APIRouter(
    prefix="/patients",
    tags=["Patient"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_patients():
    patients = await Patient.filter(data_disabled=False).all().values()

    # convert images to list
    for patient in patients:
        if patient['images'] is not None:
            patient['images'] = json.loads(patient['images'])

    # convert instructions to list
    for patient in patients:
        if patient['instructions'] is not None:
            patient['instructions'] = json.loads(patient['instructions'])

    return patients


@router.get("/patient_select")
async def get_patient_select():

    # same as staff but only take id, english_name, japanese_name, staff_group, duty_type
    patient = Patient.all()

    patient_list = await patientSelect_pydantic.from_queryset(patient)

    # dont use pydantic

    return patient_list


@router.post("/add_patient")
async def create_patient(patient_json: str = Form(...)):
    patient_data = json.loads(patient_json)

    now = datetime.now()

    patient = await Patient.create(**patient_data)

    new_patient = await patient_pydantic.from_tortoise_orm(patient)
    # new_staff = await Staff.get(id=staff.id).values()

    return new_patient


@router.put("/update_patient")
async def update_patient(patient_json: str = Form(...)):
    patient_data = json.loads(patient_json)

    data_copy = patient_data.copy()
    patient_id = data_copy.pop('id')

    await Patient.filter(id=patient_id).update(**data_copy)

    updated_patient = await patient_pydantic.from_queryset_single(Patient.get(id=patient_id))

    return updated_patient


@router.put("/delete_patients")
async def delete_patients(patient_json: str = Form(...)):
    patient_data = json.loads(patient_json)

    # update all employees in the list employees's disabled to true
    await Patient.filter(id__in=patient_data['patients']).update(data_disabled=True)
    # await Employee.filter(id__in=employe  es['ids']).delete()

    return patient_data['patients']

    # return {'msg': 'Employees deleted successfully.'}


@router.get('/download')
async def download_patient_list():
    # get all patient values but exclude id and created_at
    patient = await Patient.all().values("name_kanji", "name_kana", "birth_date", "age", "gender", "disable_support_category", "beneficiary_number", "postal_code", "prefecture",
                                         "municipality", "town", "building", "phone_number", "telephone_number", "billing_method",
                                         "billing_address", "billing_postal_code", "patient_status", "remarks")

    df = pd.DataFrame(patient)

    # headers = ["affiliation", "staff_code", "english_name", "japanese_name", "nickname", "nationality", "join_date",
    #            "leave_date", "postal_code", "prefecture", "municipality", "town",
    #            "building", "phone_number", "personal_email", "work_email", "koyou_keitai", "zaishoku_joukyou"]

    # change column headers
    headers = ["利用者名", "利用者カナ", "利用者生年月日", "年齢", "性別", "障害支援区分", "受給者番号", "郵便番号", "都道府県 ", "市区町村", "町名以下",
               "建物名", "利用者電話番号", "利用者携帯電話番号", "請求方法", "請求送付先", "請求先郵便番号", "利用者状態", "備考"]

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
            column_len = max(max_len, len(headers[i]) + 8)  # +2 for padding
            worksheet.set_column(i, i, column_len)

        excel_writer.close()  # Close the ExcelWriter to save the Excel file

    # Return the Excel file as a response
    response = FileResponse(
        tmp_file.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=patients.xlsx"

    return response


@router.put("/add_patient_images")
async def add_patient_images(patient_id: str = Form(...), images: List[UploadFile] = File(None)):
    # print(patient_id)

    now = datetime.now()
    image_list = []
    if images is not None:
        for file in images:
            print(file.filename)
            new_file_name = file.filename.split(
                '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]
            # upload to s3 bucket
            uploaded_file = upload_file_to_s3(
                file, new_file_name, s3_patients_upload_img_folder)

            s3_file_path = s3_patients_upload_img_folder + new_file_name

            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # append new urls to images list
            image_list.append(s3_read_url)

    # get patients images and convert to list
    patient = await Patient.get(id=patient_id).values('images')
    patient_images = patient['images']
    if patient_images is not None:
        patient_images = json.loads(patient_images)
        # append new images to existing images
        image_list.extend(patient_images)

    # convert to image_list to string
    image_list_str = json.dumps(image_list)

    # update patient images
    await Patient.filter(id=patient_id).update(images=image_list_str)

    # return images list and patient id in a dict
    return {'patient_id': patient_id, 'images': image_list}


@router.put("/delete_patient_images")
async def delete_patient_images(patient_id: str = Form(...), images: List[UploadFile] = File(None)):
    pass


@router.put("/add_patient_instructions")
async def add_patient_instructions(patient_json: str = Form(...), instructions_files: List[UploadFile] = File(None)):
    patient_data = json.loads(patient_json)
    now = datetime.now()

    if instructions_files is not None:
        for file in instructions_files:
            new_file_name = file.filename.split(
                '.')[0] + now.strftime("_ins_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]

            uploaded_file = upload_file_to_s3(
                file, new_file_name, s3_patients_upload_pdf_folder)

            s3_file_path = s3_patients_upload_pdf_folder + new_file_name

            s3_read_url = generate_s3_url(s3_file_path, 'read')

            # append new urls to instructions list, the intructions_files should have the same order as the instructions
            patient_data['instructions'][instructions_files.index(
                file)]['file'] = s3_read_url

    # convert to json string
    patient_data['instructions'] = json.dumps(patient_data['instructions'])

    # update patient instructions
    await Patient.filter(id=patient_data['id']).update(instructions=patient_data['instructions'])

    # convert back insturctions to list, get it from patient_pydantic
    updated_patient = await patient_pydantic.from_queryset_single(Patient.get(id=patient_data['id']))

    # only return patient id and instructions which converted back to list
    return {'patient_id': patient_data['id'], 'instructions': json.loads(updated_patient.instructions)}
