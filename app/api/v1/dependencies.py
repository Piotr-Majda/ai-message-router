from typing import Annotated

from fastapi import Depends

from app.agent.email_agent import EmailAgent
from app.core.config import config
from app.services.email_router_service import EmailRouterService
from app.services.email_service import EmailService
from app.services.smtp_email_service import SMTPEmailService


def email_service() -> EmailService:
    return SMTPEmailService(
        host=config.SMTP_HOST,
        port=config.SMTP_PORT,
        username=config.SMTP_USERNAME,
        password=config.SMTP_PASSWORD
    )

email_service_dep = Annotated[EmailService, Depends(email_service)]

def email_agent() -> EmailAgent:
    return EmailAgent(
        model_url=config.MODEL_BASE_URL, 
        model_name=config.MODEL_NAME
    )

email_agent_dep = Annotated[EmailAgent, Depends(email_agent)]

def email_router_service(email_service: email_service_dep, email_agent: email_agent_dep) -> EmailRouterService:
    return EmailRouterService(
        email_service=email_service,
        email_agent=email_agent
        )

email_router_service_dep = Annotated[EmailRouterService, Depends(email_router_service)]
