import os
import time

import httpx
import pytest

from tests.routing_cases import routing_case_by_name
from tests.smoke.conftest import SMOKE_LLM_TIMEOUT


def _base_url() -> str:
    return os.getenv("SMOKE_BASE_URL", "http://localhost:8000")


def _mailhog_api_base_url() -> str:
    return os.getenv("SMOKE_MAILHOG_API", "http://localhost:8025")


def _wait_until(predicate, timeout_s: float = 10.0, step_s: float = 0.25) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(step_s)
    raise AssertionError("condition not met within timeout")


@pytest.mark.smoke
def test_smoke_givenComposeRunning_docsAvailableAtApiV1Docs() -> None:
    with httpx.Client(base_url=_base_url(), timeout=5.0) as client:
        response = client.get("/api/v1/docs")

    assert response.status_code == 200


@pytest.mark.smoke
def test_smoke_givenComposeRunning_sendMessage_deliveredToMailhogWithReplyTo() -> None:
    base_url = _base_url()
    mailhog_api = _mailhog_api_base_url()
    it_case = routing_case_by_name("it_computer")
    sender_email = "tomek.nowak@example.com"

    with httpx.Client(timeout=SMOKE_LLM_TIMEOUT) as client:
        r = client.get(f"{mailhog_api}/api/v2/messages")
        assert r.status_code == 200
        total_messages = r.json()["total"]

        payload = {
            "email": sender_email,
            "message": it_case.user_message.message,
        }
        send_response = client.post(f"{base_url}/api/v1/messages", json=payload)

        assert send_response.status_code == 200
        body = send_response.json()
        assert body["reply_to"] == sender_email
        assert body["recipient"] == it_case.expected_recipient.value

        def new_message_arrived() -> bool:
            r = client.get(f"{mailhog_api}/api/v2/messages")
            assert r.status_code == 200
            new_counts = r.json()["total"]
            return new_counts == total_messages + 1

        _wait_until(new_message_arrived, timeout_s=10.0, step_s=1)

        latest = client.get(f"{mailhog_api}/api/v2/messages").json()["items"][0]
        headers = latest["Content"]["Headers"]
        assert headers["Reply-To"] == [sender_email]
        assert headers["To"] == [it_case.expected_recipient.value]
