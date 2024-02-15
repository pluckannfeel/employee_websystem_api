# FastAPI
from tokenize import String
from urllib.request import Request
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Request, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
import requests
import json

# cors headers
from fastapi.middleware.cors import CORSMiddleware

from app.helpers.datetime import get_date_time_now

# database
from app.db.init import initialize_db

# routers
# routers
from app.routers.users import router as userRouter
from app.routers.employees import router as employeeRouter
from app.routers.staff import router as staffRouter
from app.routers.patients import router as patientRouter
from app.routers.companies import router as companyRouter
from app.routers.medical_institutions import router as medicalInstitutionRouter
from app.routers.japan_addresses import router as japanAddressesRouter
from app.routers.shift_report import router as reportRouter
from app.routers.notifications import router as notificationRouter
from app.routers.payslip import router as payslipRouter
from app.routers.device_tokens import router as deviceTokenRouter
from app.routers.archive import router as archiveRouter

# websockets
from app.ws.connection_manager import manager as ws_manager
from urllib.parse import parse_qs, urlparse

# auth
from app.auth.authentication import verify_token_staff_code, verify_token_email
from app.auth.lineworksapi_authtoken import LineWorksAPIJWTManager

from mangum import Mangum

# onedrive
from app.helpers.onedrive import get_access_token
# import httpx

# setup loggers
# logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
# get root logger
# logger = logging.getLogger(__name__)

app = FastAPI(title="Make you Smile System API", version="0.1.1",
              description="Make You Smile Co. Ltd. System API")

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

# static file setup config
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# db
initialize_db(app)

# ROUTERS
app.include_router(staffRouter)
app.include_router(reportRouter)
app.include_router(patientRouter)
app.include_router(medicalInstitutionRouter)
app.include_router(companyRouter)
app.include_router(userRouter)
app.include_router(japanAddressesRouter)
app.include_router(notificationRouter)
app.include_router(payslipRouter)
app.include_router(deviceTokenRouter)
app.include_router(archiveRouter)

lineworkjwt = LineWorksAPIJWTManager(secret_name='LineWorksAPI_SACredentials')

# @app.websocket("/ws/notifications")
# async def websocket_endpoint(websocket: WebSocket):
#     try:
#         # Accept the WebSocket connection
#         # await websocket.accept()

#         # You can still parse and use the query parameters as needed
#         parsed_url = urlparse(str(websocket.url))
#         query_params = parse_qs(parsed_url.query)
#         token = query_params.get("token", ["anonymous"])[0]
#         client = query_params.get("client", ["web"])[0]

#         # Authentication and user identification logic
#         # Note: The logic here will depend on your application's specific requirements
#         if client == "mobile":
#             # user = await verify_token_staff_code(token)
#             user = "anonymous"
#         elif client == "web":
#             user = await verify_token_email(token)
#         else:
#             raise HTTPException(status_code=400, detail="Invalid client type")

#         # Connect the user to the WebSocket
#         await ws_manager.connect(websocket)

#         try:
#             while True:
#                 # Here you handle incoming messages
#                 data = await websocket.receive_text()
#                 print(f"Received message: {data}")
#                 # Example: Echo the received message back to the sender
#                 await ws_manager.send_personal_message(f"Echo: {data}", websocket)
#         except WebSocketDisconnect:
#             print(f"User disconnected: {user.id if user else 'anonymous'}")
#             # Disconnect the user from WebSocket
#             ws_manager.disconnect(websocket)
#             # Optionally broadcast a message to all users
#             await ws_manager.broadcast(json.dumps({"type": "user.online", "user_id": user.id if user else 'anonymous'}))

#     except Exception as e:
#         print(f"Error during WebSocket connection: {e}")
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)


origins = [
    '*',
    # "http://localhost",
    # 'http://localhost:8080',
    # 'http://localhost:3000',
    # 'http://localhost:3000/admin',
    # vite local
    # 'http://localhost:5173'
    # 'http://localhost:5173/admin'
    # 'https://mirai-cares.com',
    # 'https://mirai-cares.com/admin',
    # 'https://www.mirai-cares.com',
    # 'https://www.mirai-cares.com/admin',
    # 'https://test-deploy.d39ugbo3miv16m.amplifyapp.com/',
    # 'https://test-deploy.d39ugbo3miv16m.amplifyapp.com/admin',
]

# middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     # writes to log.txt
#     file = open('api.log', 'a+')

#     idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
#     logger.info(f"rid={idem} start request path={request.url.path}")
#     start_time = time.time()

#     response = await call_next(request)

#     process_time = (time.time() - start_time) * 1000
#     formatted_process_time = '{0:.2f}'.format(process_time)
#     logger.info(
#         f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

#     response.headers["X-Process-Time"] = str(process_time)

#     write_log = f'{get_date_time_now()} request path={request.url.path} rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code} '
#     file.write(write_log + '\n')

#     return response

# @app.get("/onedrive")
# async def test_onedrive():
#     access_token = get_access_token()

#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }

#     #TEST Folder ID
#     test = "01DNUDTEC6VHUATQYSURAIXZVT5M34KPIK"

#     # Example: List OneDrive files
#     endpoint = f'https://graph.microsoft.com/v1.0/users/adf679a5-6a9f-40ba-ba57-ccfacd751745/drive/items/{test}/children/'

#     try:
#         async with httpx.AsyncClient() as client:

#             response = await client.get(endpoint, headers=headers)

#             files = response.json()
#             return files
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=e)

# @app.post("/upload_to_onedrive")
# async def upload_file(file: UploadFile = File(...)):
#     access_token = get_access_token()

#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }

#     #TEST Folder ID
#     folder = "01DNUDTEC6VHUATQYSURAIXZVT5M34KPIK"

#      # Read the content of the uploaded file
#     file_content = await file.read()

#     # Define the endpoint to upload the file to the specified folder
#     endpoint = f'https://graph.microsoft.com/v1.0/users/adf679a5-6a9f-40ba-ba57-ccfacd751745/drive/items/{folder}/children/{file.filename}/content'

#     # async with httpx.AsyncClient() as client:
#     #     # Upload the file content
#     #     response = await client.put(endpoint, headers=headers, data=file_content)
#     #     if response.status_code == 201:
#     #         return {"message": "File uploaded successfully"}
#     #     else:
#     #         raise HTTPException(status_code=response.status_code, detail="OneDrive API request failed")

#     response = requests.put(endpoint, headers=headers, data=file_content)
#     if response.status_code == 201:
#         return {"message": "File uploaded successfully"}
#     else:
#         raise HTTPException(status_code=response.status_code, detail="OneDrive API request failed")


@app.get("/")
async def main():
    return {"message": "MYS System API"}


@app.get("/lineworksapi_data")
def get_lineworksapi_secure_data():
    jwt_token = lineworkjwt.get_jwt_token()
    # secret = lineworkjwt.get_secret()

    return {"token": jwt_token}

    # try:

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


# aws lambda
handler = Mangum(app)
