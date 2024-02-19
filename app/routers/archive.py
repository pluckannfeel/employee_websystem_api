from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3

# schema
from app.models.archive_schema import FilesToDelete

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

# helpers
from app.helpers.archive_manager import ArchiveManager


from tempfile import NamedTemporaryFile

router = APIRouter(
    prefix="/archive",
    tags=["Archive/Library"],
    responses={404: {"some_description": "Not found"}}
)

archive_manager = ArchiveManager()


@router.get("/current_directory")
async def get_current_directory(folder_path: str):
    print(folder_path)
    # get all files in the current directory
    files = archive_manager.read_directory(prefix=folder_path)

    # length
    # length = len(files)
    # print(length)
    return files


@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...), current_path: str = Form(...), user_name: str = Form(...)):
    try:

        # print(current_path)
        # print(file.filename)
        file_name = file.filename
        # # upload the file
        uploadFile = archive_manager.upload_file(
            file, file_name, current_path, last_modified_by=user_name)

        return uploadFile

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/replace_file")
async def replace_file(file: UploadFile = File(...), current_path: str = Form(...), user_name: str = Form(...)):
    try:
        file_name = file.filename
        # # upload the file
        uploadFile = archive_manager.replace_file(
            file, file_name, current_path, last_modified_by=user_name)

        return uploadFile

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create_folder")
async def create_folder(folder_name: str = Form(...), current_path: str = Form(...), user_name: str = Form(...)):
    # Assuming you have logic here to create the folder...
    try:
        # Your logic to create the folder
        createFolder = archive_manager.create_folder(
            folder_name, current_path, last_modified_by=user_name)

        return createFolder

        # if createFolder.get('code') == 'success':
        #     print("success")
        #     # return list of files in the current directory
        #     files = archive_manager.read_directory(prefix=current_path)
        #     return files
        # else:
        #     # raise error
        #     raise HTTPException(
        #         status_code=400, detail=createFolder.get('message'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete_files")
async def delete_files(files_to_delete: FilesToDelete):
    try:
        # Your logic to create the folder
        deleteFiles = archive_manager.delete_files(files_to_delete.files)

        return deleteFiles

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
