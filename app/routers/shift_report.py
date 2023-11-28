# fast api
import json
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.shift_report import Report, report_pydantic
from app.models.staff_shift import Staff_Shift, staff_shift_pydantic

# tortoise
from tortoise.exceptions import DoesNotExist

# helpers
from app.helpers.conversions import string_to_dict


router = APIRouter(
    prefix="/shift_report",
    tags=["shift_report"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_all_reports():
    # reports = await report_pydantic.from_queryset(Report.all())

    # get the reports with the staff_shift instance
    reports = await Report.all().prefetch_related('shift').values("id", "patient", "service_hours", "toilet_assistance", "meal_assistance", "bath_assistance", "grooming_assistance", "positioning_assistance", "medication_medical_care", "daily_assistance", "outgoing_assistance", "shift__staff", "shift__start", "shift__end", "created_at")

    # serialized_reports = [report.dict() for report in reports]

    # Fields to convert
    fields_to_convert = ['toilet_assistance', 'bath_assistance', 'daily_assistance',
                         'grooming_assistance', 'meal_assistance', 'medication_medical_care',
                         'outgoing_assistance', 'positioning_assistance']

    for report in reports:
        shift_data = {
            'staff': report.pop('shift__staff', None),
            'start': report.pop('shift__start', None),
            'end': report.pop('shift__end', None)
        }
        report['shift'] = shift_data

        for field in fields_to_convert:
            if field in report and report[field]:
                report[field] = string_to_dict(report[field])

    return reports


@router.get("/{shift_id}")
async def get_report_by_shiftid(shift_id: str):
    report = await Report.filter(shift_id=shift_id).first()
    if not report:
        # raise HTTPException(status_code=404, detail="Report not found")
        return None

    # Serialize using the Pydantic model
    serialized_report = await report_pydantic.from_tortoise_orm(report)
    report_dict = serialized_report.dict()

    # Fields to convert
    fields_to_convert = ['toilet_assistance', 'bath_assistance', 'daily_assistance',
                         'grooming_assistance', 'meal_assistance', 'medication_medical_care',
                         'outgoing_assistance', 'positioning_assistance']

    for field in fields_to_convert:
        if field in report_dict and report_dict[field]:
            report_dict[field] = string_to_dict(report_dict[field])

    return report_dict


@router.post("/add_shift_report")
async def create_shift_report(shift_report_json: str = Form(...)):
    report_data = json.loads(shift_report_json)

    # remove id
    report_data.pop('id', None)

    # Extract shift and validate it
    shift_id = report_data.pop('shift_id', None)
    if not shift_id:
        raise HTTPException(status_code=400, detail="Shift ID is required")

    try:
        # Fetch the Staff_Shift instance
        staff_shift = await Staff_Shift.get(id=shift_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Staff shift not found")

    # # Check if a report for this shift already exists
    existing_report = await Report.filter(shift_id=staff_shift.id).first()
    if existing_report:
        raise HTTPException(status_code=400, detail="report_exists")
    # now this will be useless because we will check if id exists in UI,
    # if its then it is understood the we will update that report.
    # it will call the update http endpoint

    # # Create the Report with the staff_shift instance
    report = await Report.create(shift_id=staff_shift.id, **report_data)

    new_report = await report_pydantic.from_tortoise_orm(report)
    return new_report


@router.put("/update_shift_report")
async def update_shift_report(shift_report_json: str = Form(...)):
    report_data = json.loads(shift_report_json)

    # remove id
    report_id = report_data.pop('id', None)

    # Extract shift and validate it
    shift_id = report_data.pop('shift_id', None)
    if not shift_id or not report_id:
        raise HTTPException(status_code=400, detail="credentials are missing.")

    try:
        # Fetch the Staff_Shift instance
        staff_shift = await Staff_Shift.get(id=shift_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Staff shift not found")

    await Report.filter(id=report_id).update(**report_data)

    serialized_report = await report_pydantic.from_queryset_single(Report.get(shift_id=staff_shift.id))

    updated_report = serialized_report.dict()

    # Fields to convert
    fields_to_convert = ['toilet_assistance', 'bath_assistance', 'daily_assistance',
                         'grooming_assistance', 'meal_assistance', 'medication_medical_care',
                         'outgoing_assistance', 'positioning_assistance']

    for field in fields_to_convert:
        if field in updated_report and updated_report[field]:
            updated_report[field] = string_to_dict(updated_report[field])

    return updated_report
