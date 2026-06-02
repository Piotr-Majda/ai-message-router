from abc import ABC, abstractmethod
from app.models.messages import EmailMessage


class EmailService(ABC):
    
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        pass