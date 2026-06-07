import pytest

from app.agent.email_agent import RouterAgentDeps, send_routed_user_email
from app.domain.constants import Department
from app.models.messages import EmailMessage, UserMessage
from tests.integration.conftest import Outbox, RecordingEmailService


@pytest.mark.integration
@pytest.mark.anyio
async def test_sendRoutedUserEmail_givenValidRecipient_sendsOnce(
    outbox: Outbox,
) -> None:
    recording_service = RecordingEmailService(outbox)
    user_message = UserMessage(
        email="jan.nowak@example.com", message="Nie działa mi komputer"
    )
    deps = RouterAgentDeps(email_service=recording_service, user_message=user_message)

    result = await send_routed_user_email(deps, Department.IT)

    assert result == "Email sent successfully."
    assert outbox.send_calls == 1
    assert deps.email_sent is True
    assert deps.sent_message == EmailMessage(
        sender_email="jan.nowak@example.com",
        recipient_email=Department.IT,
        subject="Request",
        reply_to="jan.nowak@example.com",
        body="Nie działa mi komputer",
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_sendRoutedUserEmail_givenEmailAlreadySent_doesNotSendAgain(
    outbox: Outbox,
) -> None:
    recording_service = RecordingEmailService(outbox)
    user_message = UserMessage(
        email="jan.nowak@example.com", message="Nie działa mi komputer"
    )
    deps = RouterAgentDeps(
        email_service=recording_service,
        user_message=user_message,
        email_sent=True,
        sent_message=EmailMessage(
            sender_email="jan.nowak@example.com",
            recipient_email=Department.IT,
            subject="Request",
            reply_to="jan.nowak@example.com",
            body="Nie działa mi komputer",
        ),
    )

    result = await send_routed_user_email(deps, Department.HELP_DESK)

    assert result == "Email already sent."
    assert outbox.send_calls == 0
