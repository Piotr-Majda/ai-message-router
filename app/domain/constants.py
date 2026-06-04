KADRY_EMAIL = "kadry@example.com"
HELP_DESK_EMAIL = "help-desk@example.com"
IT_EMAIL = "it@example.com"
HR_EMAIL = "human-resources@example.com"
FALLBACK_EMAIL = "other@example.com"

emails = {
    KADRY_EMAIL: {
        "name": "Kadry / payroll administration",
        "responsibilities": (
            "Use this department for employee administrative matters related to employment records, "
            "leave administration, sick leave, L4, absences, vacation requests, work certificates, "
            "contracts, payroll documents, salary slips, payslips, tax forms and employment paperwork. "
            "Typical intent: the user wants to request, report, confirm, correct or ask about an HR/payroll document "
            "or an absence from work. "
            "Examples: 'Chcę zgłosić urlop', 'Mam L4', 'Byłem u lekarza i potrzebuję dnia wolnego', "
            "'Nie zgadza mi się pasek wypłaty', 'Potrzebuję zaświadczenia o zatrudnieniu'. "
            "Do not use this department only because the message mentions an HR/payroll system. "
            "If the main problem is login, access, password, account, application error or system not working, use IT instead."
        ),
    },
    HR_EMAIL: {
        "name": "Human Resources / people operations",
        "responsibilities": (
            "Use this department for recruitment, hiring process, onboarding, employee benefits, company policies, "
            "training, workplace culture, organizational questions and general HR support. "
            "Typical intent: the user asks about people-related processes, recruitment, onboarding, benefits, policy "
            "or general employee support, not a concrete absence or payroll document. "
            "Examples: 'Chcę zapytać o benefity', 'Kiedy zaczynam onboarding?', "
            "'Mam pytanie o proces rekrutacji', 'Jak wygląda polityka pracy zdalnej?'. "
            "Do not use this department for vacation requests, sick leave, L4, payroll corrections or salary documents; "
            "those belong to Kadry."
        ),
    },
    HELP_DESK_EMAIL: {
        "name": "Help Desk / office equipment support",
        "responsibilities": (
            "Use this department for physical office equipment and workplace device issues that are not primarily "
            "about user accounts or software access. This includes printers, scanners, meeting room equipment, "
            "badges, office hardware, paper jams, printing problems and broken shared office devices. "
            "Typical intent: the user needs practical support with office equipment. "
            "Examples: 'Drukarka nie drukuje', 'Nie mogę zeskanować dokumentu', "
            "'Projektor w sali konferencyjnej nie działa', 'Zaciął się papier w drukarce'. "
            "If the problem is about login, password, VPN, computer operating system, company software or access to a system, use IT."
        ),
    },
    IT_EMAIL: {
        "name": "IT / technical systems and access",
        "responsibilities": (
            "Use this department for technical problems with computers, accounts, passwords, login, VPN, email accounts, "
            "company applications, permissions, software errors, operating system issues, network access, system access "
            "and devices assigned to a specific employee such as laptop or workstation. "
            "Typical intent: the user cannot use a digital system, cannot log in, needs technical access, "
            "has a blocked account, forgotten password, broken computer or software issue. "
            "Examples: 'Nie mogę się zalogować', 'Zapomniałem hasła', 'Konto jest zablokowane', "
            "'Nie działa mi komputer', 'Nie mam dostępu do systemu kadrowego', "
            "'VPN nie działa', 'Aplikacja firmowa wyrzuca błąd'. "
            "Important rule: if the message mentions Kadry/HR/payroll system but the actual problem is access, login, "
            "password, permissions or technical failure, route to IT."
        ),
    },
    FALLBACK_EMAIL: {
        "name": "Other / fallback",
        "responsibilities": (
            "Use this only when the user request is too vague, unrelated to the available departments, "
            "or there is not enough information to infer a responsible department. "
            "Examples: 'Mam pytanie', 'Proszę o kontakt', 'Czy ktoś może mi pomóc?', "
            "'Gdzie jest dobra restauracja obok biura?'. "
            "Do not use fallback if a reasonable department can be inferred from the user's intent."
        ),
    },
}

def departments_prompt() -> str:
    lines = [
        "You must classify the employee message by the user's MAIN INTENT.",
        "Pick exactly one recipient email from the allowed list.",
        "",
        "Allowed recipient emails:",
        *(
            f"- {address}: {meta['name']} — {meta['responsibilities']}"
            for address, meta in emails.items()
        ),
        "",
        "Decision rules:",
        f"- If the user wants to request/report absence, vacation, leave, sick leave, L4, day off, doctor visit or payroll/employment paperwork -> {KADRY_EMAIL}",
        f"- If the user asks about recruitment, onboarding, benefits, company policy or general HR topics -> {HR_EMAIL}",
        f"- If the user has a problem with printer, scanner, printing documents or shared office equipment -> {HELP_DESK_EMAIL}",
        f"- If the user has a technical problem with login, password, account, permissions, VPN, computer, software or access to any company system -> {IT_EMAIL}",
        f"- If the message is unclear, unrelated or impossible to classify -> {FALLBACK_EMAIL}",
        "",
        "Conflict resolution:",
        f"- Access/login/password/system failure always wins over department topic -> {IT_EMAIL}",
        f"- Example: 'Nie mogę zalogować się do systemu kadrowego' -> {IT_EMAIL}",
        f"- Example: 'Chcę zgłosić urlop w systemie kadrowym' -> {KADRY_EMAIL}",
        f"- Example: 'Nie działa drukarka' -> {HELP_DESK_EMAIL}",
        f"- Example: 'Chcę zapytać o benefity' -> {HR_EMAIL}",
        "",
        "Output rules:",
        "- Return exactly one email address.",
        "- Do not explain your reasoning.",
        "- Do not add any extra text.",
    ]
    return "\n".join(lines)
