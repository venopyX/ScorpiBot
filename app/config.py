"""Centralized configuration loaded from environment variables."""
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    """Typed application settings, populated once at import time."""

    bot_token: str
    api_base_url: str
    api_token: str
    ai_model: str = "@cf/meta/llama-4-scout-17b-16e-instruct"
    health_port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Feature toggles - handy for turning things off without editing code
    stickers_enabled: bool = os.getenv("STICKERS_ENABLED", "true").lower() == "true"
    reactions_enabled: bool = os.getenv("REACTIONS_ENABLED", "true").lower() == "true"

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("BOT_TOKEN", self.bot_token),
                ("API_BASE_URL", self.api_base_url),
                ("API_TOKEN", self.api_token),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required environment variable(s): {', '.join(missing)}. "
                "Copy .env.example to .env and fill them in."
            )


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    api_base_url=os.getenv("API_BASE_URL", ""),
    api_token=os.getenv("API_TOKEN", ""),
)

# Kept for any code/tests that still import the old flat names directly.
BOT_TOKEN = settings.bot_token
API_BASE_URL = settings.api_base_url
API_TOKEN = settings.api_token
