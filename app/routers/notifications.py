import requests
from fastapi import APIRouter, HTTPException, Form
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist
from datetime import datetime

import json
import httpx
# model
from app.models.notification import Notification, notification_pydantic
from app.models.device_token import Device_Token

# connection manger
from app.ws.connection_manager import manager
from typing import List

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("", response_model=List[notification_pydantic])
async def get_notifications():
    """
    Fetch all notifications.
    """
    return await notification_pydantic.from_queryset(Notification.all())

# @router.post("/notifications/", response_model=notification_pydantic)
# async def create_notification(notification_in: notification_pydantic):
#     """
#     Create a new notification.
#     """
#     notification_obj = await Notification.create(**notification_in.dict(exclude_unset=True))
#     return await notification_pydantic.from_tortoise_orm(notification_obj)


async def create_and_broadcast_notification(code, params, recipient=None):
    # Create a new notification in the database
    notification = await Notification.create(
        code=code,
        recipient=recipient,
        params=params,
        unread=True,
        # Add any other fields you need
    )

    # Serialize the notification for broadcasting
    notification_data = await notification_pydantic.from_tortoise_orm(notification)

    print(f"notifications: {notification_data}")
    # Broadcast the notification to all connected WebSocket clients
    await manager.broadcast(notification_data.json())


@router.post("/send_push_notification")
async def send_push_notification(notification_json: str = Form(...)):
    data = json.loads(notification_json)
    """
    Send a push notification to a specific staff member.
    """
    # Get the staff member's device token
    try:
        # if data["staff_code"] == "all" get all tokens
        if data["staff_code"] == "all":
            tokens = await Device_Token.all().values('token')
        else:
        # get all tokens of that staff member
            tokens = await Device_Token.filter(staff_code=data["staff_code"]).all().values('token')

        # send push notification to all tokens
        async with httpx.AsyncClient() as client:
            for token in tokens:
                response = await client.post(
                    'https://exp.host/--/api/v2/push/send',
                    json={
                        "to": token['token'],
                        "title": data["title"],
                        "body": data["body"],
                        "sound": "default",
                        "badge": 1,
                    }
                )

            return {"exception": "push notification sent"}
        # Create a new notification in the database
    except DoesNotExist:
        # do nothing
        return {"exception:": "error trying to send push notification"}
        # raise HTTPException(
        # status_code=404, detail=f"Staff member {staff_code} not found")


@router.post("/test_send_push_notification/")
def test_send_notification(token: str, title: str, body: str):
    response = requests.post(
        'https://exp.host/--/api/v2/push/send',
        json={
            "to": token,
            "title": title,
            "body": body,
            "sound": "default",
            "badge": 1,
        }
    )
    return response.json()


@router.get("/{mys_id}")
async def get_notification_by_staff(mys_id: str):
    # print(mys_id)
    """
    Fetch a specific notification by ID, filtered to only include notifications from the current month.
    """

    # Calculate the first and last day of the current month
    today = datetime.today()
    first_day_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        # If current month is December, next month is January of next year
        first_day_of_next_month = datetime(today.year + 1, 1, 1)
    else:
        # Otherwise, just increment the month
        first_day_of_next_month = datetime(today.year, today.month + 1, 1)

    # Filter notifications by recipient and by date range
    try:
        notifications = await Notification.filter(
            recipient=mys_id,
            created_at__gte=first_day_of_month,
            created_at__lt=first_day_of_next_month
        ).all().order_by('-created_at')

        return notifications
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"Notification {mys_id} not found")
