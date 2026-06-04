import asyncio
from dataclasses import dataclass

from app.agent.email_agent import EmailAgent
from app.exceptions.exceptions import EmailDeliveryFailed
from app.models.messages import EmailMessage, UserMessage
from app.services.email_service import EmailService


@dataclass
class Result:
    status: str
    email_message: EmailMessage


class EmailRouterService:

    def __init__(self, email_service: EmailService, email_agent: EmailAgent):
        self._email_service = email_service
        self._email_agent = email_agent

    async def send(self, user_message: UserMessage) -> Result:
        recipient = await self._email_agent.classify_recipient(user_message.message)
        email_message = EmailMessage(
            sender_email=user_message.email,
            recipient_email=recipient,
            subject="New support request",
            reply_to=user_message.email,
            body=user_message.message)
        try:
            await asyncio.to_thread(self._email_service.send, email_message)
        except Exception as err:
            raise EmailDeliveryFailed() from err
        return Result(status="sent", email_message=email_message)
