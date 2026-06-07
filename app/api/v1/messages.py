from fastapi import APIRouter

from app.api.v1.dependencies import email_agent_dep
from app.models.messages import UserMessage

router = APIRouter()


@router.post("/messages")
async def send_message(request: UserMessage, agent: email_agent_dep):
    email_message = await agent.route_and_send(request)
    return {
        "status": "sent",
        "recipient": email_message.recipient_email,
        "reply_to": email_message.reply_to,
    }