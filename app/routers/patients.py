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
from app.models.patient import Patient, patient_pydantic

from tempfile import NamedTemporaryFile

router = APIRouter(
    prefix="/patients",
    tags=["Patient"],
    responses={404: {"some_description": "Not found"}}
)

@router.get("")
# async def get_staff(user_email_token: str, staff_group: str):
async def get_patients():
    # you can filter by affiliation later on
    # get all patient 
    return await Patient.all().values()

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

@router.get('/download')
async def download_patient_list():
    # get all patient values but exclude id and created_at
    patient = await Patient.all().values("name_kanji", "name_kana", "birth_date", "gender", "postal_code", "prefecture",
                                    "municipality", "town", "building", "phone_number", "telephone_number", "billing_method",
                                      "billing_address", "billing_postal_code", "patient_status", "remarks")

    df = pd.DataFrame(patient)

    # headers = ["affiliation", "staff_code", "english_name", "japanese_name", "nickname", "nationality", "join_date",
    #            "leave_date", "postal_code", "prefecture", "municipality", "town",
    #            "building", "phone_number", "personal_email", "work_email", "koyou_keitai", "zaishoku_joukyou"]

    # change column headers
    headers = ["利用者名", "利用者カナ", "利用者生年月日", "性別", "郵便番号", "都道府県 ", "市区町村", "町名以下",
            "建物名", "利用者電話番号", "利用者携帯電話番号", "請求方法", "請求送付先", "請求先郵便番号", "利用者状態", "備考"]

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
            column_len = max(max_len, len(headers[i]) + 8)  # +2 for padding
            worksheet.set_column(i, i, column_len)

        excel_writer.close()  # Close the ExcelWriter to save the Excel file

    # Return the Excel file as a response
    response = FileResponse(tmp_file.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=patients.xlsx"

    return response