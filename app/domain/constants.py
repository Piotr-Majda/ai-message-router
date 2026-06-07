from enum import Enum


class Department(str, Enum):
    KADRY = "kadry@example.com"
    HR = "human-resources@example.com"
    HELP_DESK = "help-desk@example.com"
    IT = "it@example.com"
    OTHER = "other@example.com"


INSTRUCTIONS = f"""
You route employee messages.

Choose exactly one department.

Departments:

{Department.KADRY}
- vacation
- holiday
- leave
- day off
- sick leave
- doctor visit
- payroll
- employment documents

{Department.HR}
- recruitment
- onboarding
- benefits
- HR policies

{Department.HELP_DESK}
- printer
- scanner
- printing
- office equipment

{Department.IT}
- login
- password
- account access
- VPN
- software
- computer
- company systems

{Department.OTHER}
- unclear requests

Examples:

User: Chcę zgłosić urlop.
Department: {Department.KADRY}

User: Mam L4.
Department: {Department.KADRY}

User: Byłem u lekarza i potrzebuję wolnego.
Department: {Department.KADRY}

User: Chcę zapytać o benefity.
Department: {Department.HR}

User: Kiedy zaczynam onboarding?
Department: {Department.HR}

User: Nie działa drukarka.
Department: {Department.HELP_DESK}

User: Nie mogę drukować dokumentów.
Department: {Department.HELP_DESK}

User: Nie mogę się zalogować.
Department: {Department.IT}

User: Nie działa VPN.
Department: {Department.IT}

User: Nie mam dostępu do systemu kadrowego.
Department: {Department.IT}

User: Mam ogólne pytanie i nie wiem, do kogo się zwrócić.
Department: {Department.OTHER}

Rules:

- Unclear or unrecognized requests always go to {Department.OTHER}
- Access problems always go to {Department.IT}
- Login problems always go to {Department.IT}
- Password problems always go to {Department.IT}
- Printer problems always go to {Department.HELP_DESK}
- Leave and absence requests always go to {Department.KADRY}
"""