# fast api
import json
from datetime import datetime
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.device_token import Device_Token, device_token_pydantic
from app.models.staff import Staff, staff_pydantic

from typing import Optional
from tortoise.expressions import Q

# tortoise
from tortoise.exceptions import DoesNotExist

# helpers
from app.helpers.conversions import string_to_dict
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url

# s3_payslip_upload_folder = 'uploads/staff/payslip/'

router = APIRouter(
    prefix="/device_tokens",
    tags=["device_tokens"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register")
async def register_device_token(device_details_json: str = Form(...)):
    details = json.loads(device_details_json)

    # check if device token already exists, if not update the existing one
    device_token = await Device_Token.get_or_none(token=details['token'])

    if device_token:
        # update the existing device token
        await device_token.update_from_dict(details)
        await device_token.save()
    else:
        # create a new device token
        device_token = await Device_Token.create(**details)

    return await device_token_pydantic.from_tortoise_orm(device_token)
