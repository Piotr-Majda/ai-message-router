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
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None


config = Config() # type: ignore[call-arg]
