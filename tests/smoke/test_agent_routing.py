import os

import httpx
import pytest

from app.domain.constants import HELP_DESK_EMAIL, IT_EMAIL, KADRY_EMAIL


def _base_url() -> str:
    return os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000")


@pytest.mark.smoke
@pytest.mark.parametrize(
    "message,expected_recipient",
    [
        (
            "Potrzebuję wolnego jutro, bo mam wizytę u lekarza.",
            KADRY_EMAIL,
        ),
        (
            "Nie mogę drukować dokumentów i przez to nie mogę przygotować umowy.",
            HELP_DESK_EMAIL,
        ),
        (
            "Mam problem z dostępem do systemu kadrowego.",
            IT_EMAIL,
        ),
        (
            "Nie działa mi komputer",
            IT_EMAIL,
        ),
    ],
)
def test_smoke_givenRoutingMessage_agentRoutesToExpectedRecipient(
    message: str,
    expected_recipient: str,
) -> None:
    payload = {"email": "jan.nowak@example.com", "message": message}

    with httpx.Client(base_url=_base_url(), timeout=120.0) as client:
        response = client.post("/api/v1/messages", json=payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sent"
    assert body["recipient"] == expected_recipient
    assert body["reply_to"] == "jan.nowak@example.com"
