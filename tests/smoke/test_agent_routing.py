import os

import httpx
import pytest

from app.domain.constants import Department
from tests.smoke.conftest import SMOKE_LLM_TIMEOUT


def _base_url() -> str:
    return os.getenv("SMOKE_BASE_URL", "http://localhost:8000")


@pytest.mark.smoke
@pytest.mark.parametrize(
    "message,expected_recipient",
    [
        (
            "Potrzebuję wolnego jutro, bo mam wizytę u lekarza.",
            Department.KADRY,
        ),
        (
            "Chcę zapytać o benefity.",
            Department.HR,
        ),
        (
            "Nie mogę drukować dokumentów i przez to nie mogę przygotować umowy.",
            Department.HELP_DESK,
        ),
        (
            "Nie działa mi komputer",
            Department.IT,
        ),
        (
            "Mam ogólne pytanie i nie wiem, do kogo się zwrócić.",
            Department.OTHER,
        ),
    ],
)
def test_smoke_givenRoutingMessage_agentRoutesToExpectedRecipient(
    message: str,
    expected_recipient: str,
) -> None:
    payload = {"email": "jan.nowak@example.com", "message": message}

    with httpx.Client(base_url=_base_url(), timeout=SMOKE_LLM_TIMEOUT) as client:
        response = client.post("/api/v1/messages", json=payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sent"
    assert body["recipient"] == expected_recipient
    assert body["reply_to"] == "jan.nowak@example.com"
