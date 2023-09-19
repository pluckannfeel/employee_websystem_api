import logging
import random
import string
import time
from datetime import datetime

# FastAPI
from tokenize import String
from urllib.request import Request
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

# cors headers
from fastapi.middleware.cors import CORSMiddleware

from app.helpers.datetime import get_date_time_now

# database
from app.db.init import initialize_db

# routers
from app.routers.users import router as userRouter
from app.routers.employees import router as employeeRouter
from app.routers.staff import router as staffRouter
from app.routers.japan_addresses import router as japanAddressesRouter

from mangum import Mangum

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
app.include_router(userRouter)
app.include_router(staffRouter)
app.include_router(japanAddressesRouter)


origins = [
    '*',
    # "http://localhost",
    # 'http://localhost:8080',
    # 'http://localhost:3000',
    # 'http://localhost:3000/employee-web-system'
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


@app.get("/")
async def main():
    return {"message": "MYS System API"}

# aws lambda
handler = Mangum(app)

