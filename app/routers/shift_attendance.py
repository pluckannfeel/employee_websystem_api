import json
import os
import io
import re
import chardet
import calendar
import pandas as pd
import requests
import pytz

from typing import List, Type
from datetime import datetime, timedelta, timezone, time


# env
from dotenv import load_dotenv

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.staff_shift import Staff_Shift, staff_shift_pydantic
from app.models.staff import Staff

from tortoise.expressions import Q

router = APIRouter(
    prefix="/staff_attendance",
    tags=["Staff Attendance"],
    responses={404: {"staff_attendance": "Not found"}}
)


# @router.get('/shift_by_date')
# async def get_attendance_record(selected_date: str):
#     year, month = map(int, selected_date.split('-'))
#     timezone = pytz.UTC
#     first_day_of_month = datetime(year, month, 1, tzinfo=timezone)
#     last_day_of_month = datetime(year, month + 1, 1, tzinfo=timezone) - timedelta(
#         seconds=1) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)

#     shifts = await Staff_Shift.filter(
#         start__gte=first_day_of_month,
#         start__lte=last_day_of_month,
#     ).exclude(service_details='☆★☆お休み希望☆★☆').values('staff', 'patient', 'start', 'end', 'duration', 'service_details')

#     staff_members = await Staff.filter(disabled=False).exclude(Q(zaishoku_joukyou__icontains="退職") | Q(zaishoku_joukyou__icontains="退社済")).all().values('japanese_name', 'staff_code', 'nationality')

#     staff_details_mapping = {
#         staff['japanese_name']: staff for staff in staff_members}

#     attendance_records = []
#     for index, shift in enumerate(shifts):
#         start_datetime = shift['start']
#         end_datetime = shift['end']
#         staff_info = staff_details_mapping.get(shift['staff'], {})
#         attendance_record = {
#             'id': index + 1,
#             'date': start_datetime.date(),
#             'staff_code': staff_info.get('staff_code', ''),
#             'service_hours': f"{start_datetime.strftime('%H:%M')} ~ {end_datetime.strftime('%H:%M')}",
#             # Convert duration to hours and round it to 2 decimal places
#             'duration': round(float(shift['duration']) / 60, 2),
#             'patient_name': shift['patient'],
#             'service_type': shift['service_details'],
#             # Assuming 'remarks' is part of your shift data
#             'remarks': shift.get('remarks', '')
#         }
#         attendance_records.append(attendance_record)

#     # Sort the records by date
#     attendance_records.sort(key=lambda x: x['date'])

#     return attendance_records

@router.get('/shift_by_date')
async def get_attendance_record(selected_date: str):
    year, month = map(int, selected_date.split('-'))
    timezone = pytz.UTC
    first_day_of_month = datetime(year, month, 1, tzinfo=timezone)
    last_day_of_month = datetime(year, month + 1, 1, tzinfo=timezone) - timedelta(seconds=1) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)

    # Fetch shifts within the month, excluding specific service details
    shifts = await Staff_Shift.filter(
        start__gte=first_day_of_month,
        start__lte=last_day_of_month,
    ).exclude(service_details='☆★☆お休み希望☆★☆').values('staff', 'patient', 'start', 'end', 'duration', 'service_details')

    # Fetch staff members, excluding certain statuses
    staff_members = await Staff.filter(disabled=False).exclude(Q(zaishoku_joukyou__icontains="退職") | Q(zaishoku_joukyou__icontains="退社済")).values('japanese_name', 'staff_code')

    # Create a mapping from japanese_name to staff details for efficient lookups
    staff_details_mapping = {staff['japanese_name']: staff for staff in staff_members}

    attendance_records = []
    for index, shift in enumerate(shifts):
        staff_info = staff_details_mapping.get(shift['staff'], None)
        if staff_info:  # Proceed only if staff info is found
            attendance_record = {
                'id': str(index + 1),
                'date': shift['start'].date(),
                'staff_code': staff_info['staff_code'],
                'service_hours': f"{shift['start'].strftime('%H:%M')} ~ {shift['end'].strftime('%H:%M')}",
                'duration': round(float(shift['duration']) / 60, 2),
                'patient_name': shift['patient'],
                'service_type': shift['service_details'],
                'remarks': shift.get('remarks', '')
            }
            attendance_records.append(attendance_record)

    # Sort the records by date
    attendance_records.sort(key=lambda x: x['date'])

    return attendance_records
