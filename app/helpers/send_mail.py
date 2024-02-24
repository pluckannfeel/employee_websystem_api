from fastapi import FastAPI, Form, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define your email configuration
# conf = ConnectionConfig(
#     MAIL_USERNAME="jarvis@makeyousmile.jp",
#     MAIL_PASSWORD="tBB18ZEvk2fK",
#     MAIL_FROM="jarvis@makeyousmile.jp",
#     MAIL_PORT=587,
#     MAIL_SERVER="smtp.worksmobile.com",
#     MAIL_TLS=True,
#     MAIL_SSL=False,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True
# )


# async def send_email(email: EmailSchema):
#     message = MessageSchema(
#         subject=email.subject,
#         recipients=[email.email],
#         body=email.body,
#         subtype="html"
#     )

#     fm = FastMail(conf)
#     await fm.send_message(message)

#     return {"message": "email has been sent"}


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: str
    subject: str


class Mailer:
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME="jarvis@makeyousmile.jp",
            MAIL_PASSWORD="nDL2ZM62DM8c",
            # MAIL_PASSWORD="@Sivrajnallim96",
            MAIL_FROM="jarvis@makeyousmile.jp",
            # SMTP port for STARTTLS (replace with 465 if using SSL/TLS directly)
            MAIL_PORT=587,
            # SMTP server address (replace with actual SMTP server)
            MAIL_SERVER="smtp.worksmobile.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,  # Set based on your server's requirements
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True  # Be cautious with disabling certificate validation in production
        )

    async def send_email(self, email: EmailSchema):
        message = MessageSchema(
            subject=email.subject,
            recipients=email.email,  # List of recipients, as per Pydantic model
            body=email.body,
            subtype="html"
        )
        fm = FastMail(self.config)
        await fm.send_message(message)
        return {"message": "Mail sent successfully"}

# class Mailer:
#     def __init__(self):
#         self.server = "smtp.worksmobile.com"
#         self.port = "587"
#         self.username = "jarvis@makeyousmile.jp"
#         self.password = "nDL2ZM62DM8c"

#     async def send_email(self, email, subject, body):
#         msg = MIMEMultipart()
#         msg['From'] = self.username
#         msg['To'] = email
#         msg['Subject'] = subject
#         msg.attach(MIMEText(body, 'html'))

#         with smtplib.SMTP(self.server, self.port) as server:
#             server.starttls()
#             server.login(self.username, self.password)
#             server.sendmail(self.username, email, msg.as_string())
#         return {"message": "Mail sent successfully"}
