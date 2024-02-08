from fastapi import FastAPI, Form, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.models.email import EmailSchema

# Define your email configuration
conf = ConnectionConfig(
    MAIL_USERNAME="makeyousmile304@gmail.com",
    MAIL_PASSWORD="Makeyousmile2018",
    MAIL_FROM="makeyousmile304@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_email(email: EmailSchema):
    message = MessageSchema(
        subject=email.subject,
        recipients=[email.email],
        body=email.body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "email has been sent"}
