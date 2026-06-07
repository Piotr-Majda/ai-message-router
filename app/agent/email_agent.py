import asyncio
from dataclasses import dataclass
from typing import Optional

from pydantic_ai import Agent, AgentRunError, RunContext, Tool
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from app.agent.email_agent_protocol import EmailAgentProtocol
from app.core.logging import setup_logging
from app.domain.constants import Department, INSTRUCTIONS
from app.exceptions.exceptions import (
    AgentFailedRouteMessage,
    AgentUnavailable,
    EmailDeliveryFailed,
)
from app.models.messages import EmailMessage, UserMessage
from app.services.email_service import EmailService

logger = setup_logging("EmailAgent")


@dataclass
class RouterAgentDeps:
    email_service: EmailService
    user_message: UserMessage
    email_sent: bool = False
    sent_message: Optional[EmailMessage] = None


async def send_routed_user_email(
    deps: RouterAgentDeps,
    recipient_email: Department,
) -> str:
    if deps.email_sent:
        return "Email already sent."

    email_message = EmailMessage(
        sender_email=deps.user_message.email,
        recipient_email=recipient_email,
        subject="Request",
        reply_to=deps.user_message.email,
        body=deps.user_message.message,
    )

    try:
        await asyncio.to_thread(deps.email_service.send, email_message)
    except Exception as err:
        raise EmailDeliveryFailed() from err

    deps.email_sent = True
    deps.sent_message = email_message

    return "Email sent successfully."


async def send_user_email_to_department(
    ctx: RunContext[RouterAgentDeps],
    recipient_email: Department,
) -> str:
    """Send the user's message to exactly one department inbox.

    Call this tool exactly once after choosing the department.
    Do not call again if email was already sent.

    Args:
        recipient_email: Target department inbox from the allowed list.
            Use other@example.com when the request is unclear or unrecognized.
    """
    return await send_routed_user_email(ctx.deps, recipient_email)


class EmailAgent(EmailAgentProtocol):

    def __init__(
        self, model_name: str, model_url: str, email_service: EmailService
    ) -> None:
        model = OllamaModel(
            model_name=model_name,
            provider=OllamaProvider(base_url=model_url),
            # settings=ModelSettings()
        )
        self._email_service = email_service

        self.router_agent = Agent(
            model,
            output_type=str,
            deps_type=RouterAgentDeps,
            retries=3,
            tools=[Tool(send_user_email_to_department, takes_ctx=True)],
            instructions=INSTRUCTIONS,
        )

    async def route_and_send(self, user_message: UserMessage) -> EmailMessage:
        deps = RouterAgentDeps(
            email_service=self._email_service, user_message=user_message
        )
        try:
            result = await self.router_agent.run(user_message.message, deps=deps)
        except AgentRunError as err:
            raise AgentUnavailable(f"Detail: {err.args}")
        logger.info(f"Agent finish with result {result.output}")
        if deps.sent_message is not None:
            logger.info("Routed message to %s", deps.sent_message.recipient_email)
            return deps.sent_message
        logger.error(
            "Agent failed to route user message. Message history: %s",
            result.all_messages_json(),
        )
        raise AgentFailedRouteMessage()
