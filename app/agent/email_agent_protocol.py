from typing import Protocol

from app.models.messages import UserMessage, EmailMessage

class EmailAgentProtocol(Protocol):

    async def route_and_send(self, user_message: UserMessage) -> EmailMessage:
        ...
