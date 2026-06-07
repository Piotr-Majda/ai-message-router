from typing import Protocol
from app.models.messages import EmailMessage


class EmailService(Protocol):

    def send(self, message: EmailMessage) -> None:
        pass
