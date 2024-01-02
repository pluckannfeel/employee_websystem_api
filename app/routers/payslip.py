# fast api
import json
from datetime import datetime
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from typing import List

from app.models.staff_payslip import Staff_Payslip, staff_payslip_pydantic
from app.models.staff import Staff, staff_pydantic

from typing import Optional
from tortoise.expressions import Q

# tortoise
from tortoise.exceptions import DoesNotExist

# helpers
from app.helpers.conversions import string_to_dict
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url

s3_payslip_upload_folder = 'uploads/staff/payslip/'

router = APIRouter(
    prefix="/payslip",
    tags=["staff_payslip"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_payslips_by_month_year(month: Optional[int] = None, year: Optional[int] = None):
    # query = Q()
    # if month:
    #     query &= Q(payslip_date__month=month)
    # if year:
    #     query &= Q(payslip_date__year=year)

    # get all payslips but get the staff details with staff id temporarily
    payslips = await Staff_Payslip.all().prefetch_related('staff').order_by('-created_at').values("id", "staff__id", "staff__japanese_name", "release_date", "file_url", "created_at")
    if not payslips:
        return []
        # raise HTTPException(
        #     status_code=404, detail="No payslips found for the given month and year")

    # # add staff object
    for payslip in payslips:
        staff_data = {
            'id': payslip.pop('staff__id', None),
            'japanese_name': payslip.pop('staff__japanese_name', None),
        }
        payslip['staff'] = staff_data

    return payslips
    # serialized_payslips = [await staff_payslip_pydantic.from_tortoise_orm(payslip) for payslip in payslips]
    # return serialized_payslips


@router.get("/{mys_id}")
async def get_payslips(mys_id: str):
    staff = await Staff.get(staff_code=mys_id, leave_date=None).values('id')
    if not staff:
        raise HTTPException(status_code=400, detail="Invalid staff code.")

    payslips = await Staff_Payslip.filter(staff_id=staff["id"])\
        .values("id", "net_salary", "total_deduction", "total_hours", "release_date", "file_url", "created_at")

    if not payslips:
        return []

    return payslips


@router.post("/add_payslip")
async def create_payslip(payslip_json: str = Form(...), payslip_file: UploadFile = File(None)):
    payslip_data = json.loads(payslip_json)

    # extract the staff as staff object
    staff_object = payslip_data.pop('staff', None)
    staff_id = staff_object['id']

    # check if staff exists
    try:
        staff = await Staff.get(id=staff_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Staff not found")

    now = datetime.now()

    # upload the file
    if payslip_file is not None:
        new_file_name = payslip_file.filename.split(
            '.')[0] + now.strftime("_%Y%m") + '.' + payslip_file.filename.split('.')[-1]

        upload_file = upload_file_to_s3(
            payslip_file, new_file_name, s3_payslip_upload_folder)

        s3_file_path = s3_payslip_upload_folder + new_file_name

        s3_read_url = generate_s3_url(s3_file_path, 'read')

        print(s3_read_url)

        payslip_data['file_url'] = s3_read_url

        # create the payslip
    payslip = await Staff_Payslip.create(**payslip_data, staff=staff)

    new = await staff_payslip_pydantic.from_tortoise_orm(payslip)

    # create a new payslip object with the staff object
    new_payslip = new.dict()
    new_payslip['staff'] = staff_object
    # add back the staff object

    return new_payslip


@router.delete("/delete_payslip")
async def delete_payslip(payslip_ids: List[str] = Form(...)):
    deleted_payslips = await Staff_Payslip.filter(id__in=payslip_ids).delete()
    
    if deleted_payslips == 0:
        raise HTTPException(status_code=404, detail="Payslips not found")

    return {"deleted_payslip_ids": payslip_ids}
