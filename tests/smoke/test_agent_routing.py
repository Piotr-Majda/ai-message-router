import os

import httpx
import pytest

from tests.routing_cases import ROUTING_CASES
from tests.smoke.conftest import SMOKE_LLM_TIMEOUT


def _base_url() -> str:
    return os.getenv("SMOKE_BASE_URL", "http://localhost:8000")


@pytest.mark.smoke
@pytest.mark.parametrize(
    "routing_case",
    ROUTING_CASES,
    ids=[case.name for case in ROUTING_CASES],
)
def test_smoke_givenRoutingMessage_agentRoutesToExpectedRecipient(routing_case) -> None:
    payload = {
        "email": routing_case.user_message.email,
        "message": routing_case.user_message.message,
    }

    with httpx.Client(base_url=_base_url(), timeout=SMOKE_LLM_TIMEOUT) as client:
        response = client.post("/api/v1/messages", json=payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sent"
    assert body["recipient"] == routing_case.expected_recipient.value
    assert body["reply_to"] == routing_case.user_message.email
