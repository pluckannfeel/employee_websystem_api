# models
from app.models.japan_addresses import JP_Addresses
from app.models.user import User, user_pydantic

from datetime import datetime
import shutil
import os
import time
import json

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, Form, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/jp_addresses",
    tags=["Japan Addresses"],
    responses={404: {"some_description": "Not found"}}
)

# get all postal codes
@router.get("/postal_codes", status_code=status.HTTP_200_OK)
async def get_postal_codes():
    postal_codes = await JP_Addresses.filter(jp_prefecture__in=('東京都', '神奈川県')).order_by('jp_prefecture').distinct().values('postal_code', 'en_prefecture', 'jp_prefecture', 'en_municipality','jp_municipality', 'en_town', 'jp_town')

    return postal_codes

# get all prefectures
@router.get("/prefectures", status_code=status.HTTP_200_OK)
async def get_prefectures():

    # if language == 'en':
    #     # show only prefectures that are in ('TOKYO TO', 'KANAGAWA KEN')
    #     prefectures = await JP_Addresses.filter(en_prefecture__in=('TOKYO TO', 'KANAGAWA KEN')).order_by('jp_prefecture').distinct().values('en_prefecture','jp_prefecture')
    # elif language == 'jp':
    #     #  prefectures = await JP_Addresses.filter(jp_prefecture__in=('東京都', '神奈川県')).distinct().values('jp_prefecture').order_by('jp_prefecture')
    #     prefectures = await JP_Addresses.filter(jp_prefecture__in=('東京都', '神奈川県')).order_by('jp_prefecture').distinct().values('en_prefecture','jp_prefecture')
    # else:
    #     prefectures = []

    prefectures = await JP_Addresses.filter(jp_prefecture__in=('東京都', '神奈川県')).order_by('jp_prefecture').distinct().values('en_prefecture','jp_prefecture')

    return prefectures
    

# get all municipalities
@router.get("/municipalities", status_code=status.HTTP_200_OK)
async def get_municipalities():
    municipalities = await JP_Addresses.filter(jp_prefecture__in=('東京都', '神奈川県')).order_by('jp_municipality').distinct().values('jp_prefecture', 'en_municipality','jp_municipality')

    return municipalities

# get all towns
@router.get("/towns", status_code=status.HTTP_200_OK)
async def get_towns(language: str):
    pass
