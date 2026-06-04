from fastapi import APIRouter, HTTPException

from app.models.messages import UserMessage
from app.api.v1.dependencies import email_router_service_dep

router = APIRouter()


@router.post("/messages")
async def send_message(request: UserMessage, service: email_router_service_dep):
    result = await service.send(request)
    email_message = result.email_message
    return {"status": result.status, "recipient": email_message.recipient_email, "reply_to": email_message.reply_to}
