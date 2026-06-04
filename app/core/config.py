from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Config(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "AIMessageRouter"
    debug: bool = False
    # Defaults match local MailHog; override via env in Docker/production.
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    MODEL_BASE_URL: str = "http://localhost:11434/v1"
    MODEL_NAME: str = "llama3.2:3b"
    LOGFIRE_ENABLED: bool = False
    LOGFIRE_TOKEN: Optional[str] = None


config = Config() # type: ignore[call-arg]
