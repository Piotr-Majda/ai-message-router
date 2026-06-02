import smtplib
from typing import Any

import pytest

from app.models.messages import EmailMessage
from app.services.smtp_email_service import SMTPEmailService


class _FakeSMTP:
    def __init__(self, host: str, port: int, *_: Any, **__: Any) -> None:
        self.host = host
        self.port = port
        self.sent_messages: list[Any] = []
        self.starttls_calls = 0
        self.login_calls: list[tuple[str, str]] = []

    def __enter__(self) -> "_FakeSMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def starttls(self) -> None:
        self.starttls_calls += 1

    def login(self, username: str, password: str) -> None:
        self.login_calls.append((username, password))

    def send_message(self, message: Any) -> None:
        self.sent_messages.append(message)


@pytest.mark.integration
def test_smtpEmailService_givenEmailMessage_sendsWithReplyTo(monkeypatch) -> None:
    fake_smtp = _FakeSMTP("unused", 0)

    def smtp_factory(host: str, port: int) -> _FakeSMTP:
        fake_smtp.host = host
        fake_smtp.port = port
        return fake_smtp

    monkeypatch.setattr(smtplib, "SMTP", smtp_factory)

    service = SMTPEmailService(host="mailhog", port=1025)
    message = EmailMessage(
        sender_email="jan.nowak@example.com",
        recipient_email="it@example.com",
        subject="New support request",
        reply_to="jan.nowak@example.com",
        body="Hello",
    )

    service.send(message)

    assert fake_smtp.host == "mailhog"
    assert fake_smtp.port == 1025
    assert len(fake_smtp.sent_messages) == 1
    sent = fake_smtp.sent_messages[0]
    assert sent["Reply-To"] == "jan.nowak@example.com"

