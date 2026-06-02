from typing import Annotated

from fastapi import Depends

from app.core.config import config
from app.services.email_service import EmailService
from app.services.smtp_email_service import SMTPEmailService


def email_service() -> EmailService:
    return SMTPEmailService(
        host=config.SMTP_HOST,
        port=config.SMTP_PORT,
        username=config.smtp_username,
        password=config.smtp_password
    )

email_service_dep = Annotated[EmailService, Depends(email_service)]
