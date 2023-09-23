import os
import httpx
import requests

#
# from authlib.integrations.httpx_client import OAuth2Client 
from msal import ConfidentialClientApplication
from fastapi import HTTPException
from io import BytesIO

# authority = os.environ['OD_AUTHORITY']
CLIENT_ID = os.environ['OD_CLIENT_ID']
CLIENT_SECRET = os.environ['OD_CLIENT_SECRET']
# # Define the scope with /.default suffix
# # SCOPES = ["api://f290a97f-1660-4694-ae02-01d509c1fb37/mys/.default"]
# SCOPES = ['User.Read', 'Files.ReadWrite.All']
SCOPES = ["https://graph.microsoft.com/.default"]
TENANT_ID = "34af73b3-65c7-403c-9357-80482b648278"

AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}/"

app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY_URL,
        client_credential=CLIENT_SECRET,
    )

def get_access_token():
    # Get an access token using client credentials flow
    token_response = app.acquire_token_silent(scopes=SCOPES, account=None)
    if not token_response:
        token_response = app.acquire_token_for_client(scopes=SCOPES)
        
    return token_response['access_token']

def upload_file_to_onedrive(file_content: BytesIO, file_name):
    access_token = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    #TEST Folder ID
    folder = "01DNUDTEC6VHUATQYSURAIXZVT5M34KPIK"

    # Define the endpoint to upload the file to the specified folder
    endpoint = f'https://graph.microsoft.com/v1.0/users/adf679a5-6a9f-40ba-ba57-ccfacd751745/drive/items/{folder}/children/{file_name}/content'

    # async with httpx.AsyncClient() as client:
    #     # Upload the file content
    #     response = await client.put(endpoint, headers=headers, data=file_content)
    #     if response.status_code == 201:
    #         return {"message": "File uploaded successfully"}
    #     else:
    #         raise HTTPException(status_code=response.status_code, detail="OneDrive API request failed")
        
    response = requests.put(endpoint, headers=headers, data=file_content.getvalue())
    if response.status_code == 201:
        return {"message": "File uploaded successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail="OneDrive API request failed")
    
async def read_from_onedrive():
    access_token = get_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    #TEST Folder ID
    test = "01DNUDTEC6VHUATQYSURAIXZVT5M34KPIK"

    # Example: List OneDrive files
    endpoint = f'https://graph.microsoft.com/v1.0/users/adf679a5-6a9f-40ba-ba57-ccfacd751745/drive/items/{test}/children/'
    
    try:
        async with httpx.AsyncClient() as client:

            response = await client.get(endpoint, headers=headers)
            
            files = response.json()
            return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)