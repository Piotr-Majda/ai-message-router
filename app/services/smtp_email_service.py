import smtplib
from email.message import EmailMessage as SMTPEmailMessage

from app.models.messages import EmailMessage
from app.services.email_service import EmailService


class SMTPEmailService(EmailService):
    def __init__(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def send(self, message: EmailMessage) -> None:
        email = SMTPEmailMessage()
        email["From"] = message.sender_email
        email["To"] = message.recipient_email
        email["Subject"] = message.subject

        if message.reply_to:
            email["Reply-To"] = message.reply_to

        email.set_content(message.body)

        with smtplib.SMTP(self.host, self.port) as smtp:
            if self.username and self.password:
                smtp.starttls()
                smtp.login(self.username, self.password)

            smtp.send_message(email)
