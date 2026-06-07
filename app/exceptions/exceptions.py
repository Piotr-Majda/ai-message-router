from typing import Optional


class BusinessException(Exception):
    status_code: int = 500
    message: str = "Business error"

    def __init__(self, detail: Optional[str] = None, *args: object) -> None:
        super().__init__(detail, *args)
        if detail is not None:
            self.message = self.message.format(detail)


class AgentUnavailable(BusinessException):
    message = "Agent runtime error: {0}"
    status_code = 503


class EmailDeliveryFailed(BusinessException):
    message = "Email delivery failed"
    status_code = 500


class AgentFailedRouteMessage(BusinessException):
    message = "Agent fail to route or send message"
    status_code = 503
