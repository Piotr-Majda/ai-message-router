from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, EmailStr


def validate_message(message: str) -> str:
    normalized = message.lower()
    suspicious_markers = (
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "reveal instructions",
        "jailbreak",
    )
    if any(marker in normalized for marker in suspicious_markers):
        raise ValueError("message rejected: potential prompt-injection content")
    return message


class UserMessage(BaseModel):
    email: EmailStr
    message: Annotated[str, BeforeValidator(validate_message)]


class EmailMessage(BaseModel):
    sender_email: EmailStr
    recipient_email: EmailStr
    subject: str
    reply_to: Optional[str]
    body: str
