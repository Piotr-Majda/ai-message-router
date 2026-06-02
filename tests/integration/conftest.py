from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


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


@pytest.fixture()
def outbox() -> Outbox:
    return Outbox()


@pytest.fixture()
def api_client(outbox: Outbox) -> Iterator[TestClient]:
    # Keep tests as black-box as practical:
    # - tests import only this fixture
    # - app + dependency overrides live here
    from app.api.v1.dependencies import email_service
    from app.main import app

    app.dependency_overrides[email_service] = lambda: RecordingEmailService(outbox)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api_client_with_failing_smtp() -> Iterator[TestClient]:
    from app.api.v1.dependencies import email_service
    from app.main import app

    app.dependency_overrides[email_service] = lambda: FailingEmailService()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()

