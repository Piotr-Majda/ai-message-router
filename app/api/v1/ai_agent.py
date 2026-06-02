from fastapi import APIRouter, HTTPException

from app.models.messages import EmailMessage, SendMessage
from app.api.v1.dependencies import email_service_dep

router = APIRouter()


@router.post("/messages")
async def send_message(message: SendMessage, service: email_service_dep):
    try:
        recipent = "it@example.com"
        email_message = EmailMessage(
            sender_email=message.email, 
            recipient_email=recipent,
            subject="New support request",
            reply_to=message.email,
            body=message.message)
        service.send(email_message)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Internal service error detail: {err.args}")
    return {"status": f"sent", "recipient": email_message.recipient_email, "reply_to": email_message.reply_to}