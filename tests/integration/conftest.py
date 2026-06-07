from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.agent.email_agent import EmailAgent
from app.api.v1.dependencies import email_agent, email_service
from app.domain.constants import Department
from app.exceptions.exceptions import AgentFailedRouteMessage, AgentUnavailable, EmailDeliveryFailed
from app.main import app
from app.models.messages import EmailMessage, UserMessage
from app.services.email_service import EmailService


@dataclass
class Outbox:
    send_calls: int = 0
    last_message: EmailMessage | None = None


class RecordingEmailService(EmailService):
    def __init__(self, outbox: Outbox) -> None:
        self._outbox = outbox

    def send(self, message: EmailMessage) -> None:
        self._outbox.send_calls += 1
        self._outbox.last_message = message


class FailingEmailService(EmailService):
    def send(self, message: object) -> None:
        raise RuntimeError("smtp server not available")


class FakeEmailAgent:
    """Deterministic routing for API integration tests (no Ollama)."""

    def __init__(self, email_service: RecordingEmailService | FailingEmailService) -> None:
        self._email_service = email_service

    async def route_and_send(self, user_message: UserMessage) -> EmailMessage:
        recipient = self._resolve_department(user_message.message)
        email_message = EmailMessage(
            sender_email=user_message.email,
            recipient_email=recipient,
            subject="Request",
            reply_to=user_message.email,
            body=user_message.message,
        )
        try:
            self._email_service.send(email_message)
        except Exception as err:
            raise EmailDeliveryFailed() from err
        return email_message

    def _resolve_department(self, message: str) -> Department:
        normalized = message.lower()

        if any(marker in normalized for marker in ("drukować", "drukow", "druk", "drukarka")):
            return Department.HELP_DESK

        if any(marker in normalized for marker in ("wolnego", "urlop", "lekarz", "wizyt")):
            return Department.KADRY

        if any(marker in normalized for marker in ("benefit", "onboarding", "rekrut")):
            return Department.HR

        if "dostęp" in normalized or any(
            marker in normalized for marker in ("logowanie", "hasło", "konto")
        ):
            return Department.IT

        if any(marker in normalized for marker in ("komputer", "nie działa", "system")):
            return Department.IT

        if any(
            marker in normalized
            for marker in ("ogólne pytanie", "nie wiem, do kogo", "nie wiem do kogo")
        ):
            return Department.OTHER

        return Department.IT


class NoToolEmailAgent:
    """Simulates an agent run that finishes without calling the send tool."""

    async def route_and_send(self, user_message: UserMessage) -> EmailMessage:
        raise AgentFailedRouteMessage()


class FailingEmailAgent:
    async def route_and_send(self, user_message: UserMessage) -> EmailMessage:
        raise AgentUnavailable("test agent failure")


@pytest.fixture()
def outbox() -> Outbox:
    return Outbox()


@pytest.fixture()
def api_client(outbox: Outbox) -> Iterator[TestClient]:
    recording_service = RecordingEmailService(outbox)
    app.dependency_overrides[email_service] = lambda: recording_service
    app.dependency_overrides[email_agent] = lambda: FakeEmailAgent(recording_service)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failing_smtp(outbox: Outbox) -> Iterator[TestClient]:
    failing_service = FailingEmailService()
    app.dependency_overrides[email_service] = lambda: failing_service
    app.dependency_overrides[email_agent] = lambda: FakeEmailAgent(failing_service)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failed_route(outbox: Outbox) -> Iterator[TestClient]:
    recording_service = RecordingEmailService(outbox)
    app.dependency_overrides[email_service] = lambda: recording_service
    app.dependency_overrides[email_agent] = lambda: NoToolEmailAgent()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failing_agent(outbox: Outbox) -> Iterator[TestClient]:
    recording_service = RecordingEmailService(outbox)
    app.dependency_overrides[email_service] = lambda: recording_service
    app.dependency_overrides[email_agent] = lambda: FailingEmailAgent()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
