from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import email_agent, email_service
from app.domain.constants import (
    HELP_DESK_EMAIL,
    IT_EMAIL,
    KADRY_EMAIL,
)
from app.exceptions.exceptions import AgentUnavailable
from app.main import app



@dataclass
class Outbox:
    send_calls: int = 0
    last_message: object | None = None


class RecordingEmailService:
    def __init__(self, outbox: Outbox) -> None:
        self._outbox = outbox

    def send(self, message: object) -> None:
        self._outbox.send_calls += 1
        self._outbox.last_message = message


class FailingEmailService:
    def send(self, message: object) -> None:
        raise RuntimeError("smtp server not available")


class FakeEmailAgent:
    """Deterministic routing for API integration tests (no Ollama)."""

    async def classify_recipient(self, message: str) -> str:
        normalized = message.lower()

        if any(marker in normalized for marker in ("drukować", "drukow", "druk", "drukarka")):
            return HELP_DESK_EMAIL

        if any(marker in normalized for marker in ("wolnego", "urlop", "lekarz", "wizyt")):
            return KADRY_EMAIL

        if "dostęp" in normalized or any(
            marker in normalized for marker in ("logowanie", "hasło", "konto")
        ):
            return IT_EMAIL

        if any(marker in normalized for marker in ("komputer", "nie działa", "system")):
            return IT_EMAIL

        return IT_EMAIL


class FailingEmailAgent:
    async def classify_recipient(self, message: str) -> str:
        raise AgentUnavailable("test agent failure")


@pytest.fixture()
def outbox() -> Outbox:
    return Outbox()


@pytest.fixture()
def api_client(outbox: Outbox) -> Iterator[TestClient]:
    app.dependency_overrides[email_service] = lambda: RecordingEmailService(outbox)
    app.dependency_overrides[email_agent] = lambda: FakeEmailAgent()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failing_smtp(outbox: Outbox) -> Iterator[TestClient]:
    app.dependency_overrides[email_service] = lambda: FailingEmailService()
    app.dependency_overrides[email_agent] = lambda: FakeEmailAgent()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failing_agent(outbox: Outbox) -> Iterator[TestClient]:
    app.dependency_overrides[email_service] = lambda: RecordingEmailService(outbox)
    app.dependency_overrides[email_agent] = lambda: FailingEmailAgent()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
