from dataclasses import dataclass

from app.domain.constants import Department
from app.models.messages import UserMessage


@dataclass(frozen=True)
class RoutingCase:
    name: str
    user_message: UserMessage
    expected_recipient: Department


ROUTING_CASES: tuple[RoutingCase, ...] = (
    RoutingCase(
        name="kadry_doctor_visit",
        user_message=UserMessage(
            email="jan.nowak@example.com",
            message="Potrzebuję wolnego jutro, bo mam wizytę u lekarza.",
        ),
        expected_recipient=Department.KADRY,
    ),
    RoutingCase(
        name="hr_benefits",
        user_message=UserMessage(
            email="jan.nowak@example.com",
            message="Chcę zapytać o benefity.",
        ),
        expected_recipient=Department.HR,
    ),
    RoutingCase(
        name="help_desk_printing",
        user_message=UserMessage(
            email="jan.nowak@example.com",
            message=(
                "Nie mogę drukować dokumentów i przez to nie mogę przygotować umowy."
            ),
        ),
        expected_recipient=Department.HELP_DESK,
    ),
    RoutingCase(
        name="it_computer",
        user_message=UserMessage(
            email="jan.nowak@example.com",
            message="Nie działa mi komputer",
        ),
        expected_recipient=Department.IT,
    ),
    RoutingCase(
        name="other_general_question",
        user_message=UserMessage(
            email="jan.nowak@example.com",
            message="Mam ogólne pytanie i nie wiem, do kogo się zwrócić.",
        ),
        expected_recipient=Department.OTHER,
    ),
)


def routing_case_by_name(name: str) -> RoutingCase:
    for case in ROUTING_CASES:
        if case.name == name:
            return case
    raise KeyError(f"Unknown routing case: {name}")
