from typing import Annotated

from pydantic import BaseModel, BeforeValidator
from pydantic_ai import Agent, AgentRunError
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from app.core.logging import setup_logging
from app.domain.constants import departments_prompt, emails
from app.exceptions.exceptions import AgentUnavailable

logger = setup_logging("EmailAgent")


def validate_proper_email(email: str) -> str:
    if email not in emails:
        raise ValueError(f"Email '{email}' is not valid. Choose from: {list(emails.keys())}")
    return email


class DepartmentEmail(BaseModel):
    email: Annotated[str, BeforeValidator(validate_proper_email)]


class EmailAgent:

    def __init__(self, model_name: str, model_url: str) -> None:
        model = OllamaModel(
            model_name=model_name,
            provider=OllamaProvider(base_url=model_url),
            # settings=ModelSettings()
        )

        self.agent = Agent(
            model,
            output_type=DepartmentEmail,
            retries=3,
            instructions=(
                "You are an employee message routing agent.\n"
                "Your job is to understand the user's intent and route the message to the correct department.\n"
                "Do not classify by single keywords only. Prefer semantic meaning and user intent.\n\n"
                f"{departments_prompt()}"
            ),
        )

    async def classify_recipient(self, message: str) -> str:
        try:
            result = await self.agent.run(message)
        except AgentRunError as err:
            raise AgentUnavailable(f"Detail: {err.args}")
        email = result.output.email
        logger.info("Routed message to %s", email)
        return email
