"""Health check endpoints for deployment monitoring."""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import Response as FastAPIResponse

from app.config import settings
from app.core.constants import TRIGGER_KEYWORDS
from app.services.ai_client import get_ai_client

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Princess Selene Bot Health API",
    description="Health monitoring endpoints for Princess Selene Telegram Bot",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def _no_cache_headers(extra: dict) -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        **extra,
    }


@app.get("/", summary="API Health Check")
@app.head("/", summary="API Health Check HEAD")
async def root(request: Request):
    if request.method == "HEAD":
        return FastAPIResponse(
            status_code=200,
            headers=_no_cache_headers({"X-Health-Status": "OK", "X-Service": "PrincessSeleneBot", "X-Version": "2.0.0"}),
        )

    return {
        "message": "\U0001F451 Princess Selene Bot v2.0 is running!",
        "version": "2.0.0",
        "status": "healthy",
        "docs": "/docs",
        "bot_type": "telegram",
        "features": {
            "multilingual_support": True,
            "ai_responses": True,
            "group_chat": True,
            "private_chat": True,
            "sticker_replies": settings.stickers_enabled,
            "emoji_reactions": settings.reactions_enabled,
        },
    }


@app.get("/health", summary="Detailed Health Check")
@app.head("/health", summary="Detailed Health Check HEAD")
async def health_check(request: Request):
    try:
        service_status = "healthy" if get_ai_client().health_check() else "degraded"
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        service_status = "unhealthy"

    config_status = "healthy" if all([settings.bot_token, settings.api_base_url, settings.api_token]) else "unhealthy"
    overall_status = "healthy" if service_status == "healthy" and config_status == "healthy" else "degraded"

    if request.method == "HEAD":
        status_code = 200 if overall_status == "healthy" else 503
        return FastAPIResponse(
            status_code=status_code,
            headers=_no_cache_headers(
                {
                    "X-Health-Status": overall_status.upper(),
                    "X-Service": "PrincessSeleneBot",
                    "X-Version": "2.0.0",
                    "X-AI-Status": service_status.upper(),
                    "X-Config-Status": config_status.upper(),
                    "X-Timestamp": str(int(time.time())),
                }
            ),
        )

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "version": "2.0.0",
        "bot_type": "telegram",
        "services": {
            "ai_api": service_status,
            "configuration": config_status,
            "telegram_polling": "active",
        },
        "features": {
            "language_detection": "active",
            "translation": "active",
            "message_history": "active",
            "sticker_replies": "active" if settings.stickers_enabled else "disabled",
            "emoji_reactions": "active" if settings.reactions_enabled else "disabled",
            "personality": "Princess Selene",
        },
    }


@app.head("/ping", summary="Simple Ping Check")
async def ping_check():
    return FastAPIResponse(
        status_code=200,
        headers=_no_cache_headers({"Content-Type": "text/plain", "X-Health-Status": "OK", "X-Service": "PrincessSeleneBot", "X-Ping": "PONG"}),
    )


@app.get("/ping", summary="Simple Ping Check GET")
async def ping_check_get():
    return {"status": "OK", "message": "PONG", "timestamp": time.time(), "service": "PrincessSeleneBot"}


@app.get("/status", summary="Bot Status Information")
async def bot_status():
    return {
        "bot_name": "Princess Selene",
        "personality": "Cute, flirty, and playful",
        "creator": "@venopyx",
        "languages_supported": ["English", "Amharic", "Afan Oromo"],
        "chat_types": ["private", "group"],
        "trigger_keywords": TRIGGER_KEYWORDS,
        "features": {
            "ai_powered_responses": True,
            "multilingual_support": True,
            "message_history": True,
            "auto_translation": True,
            "context_awareness": True,
            "sticker_replies": settings.stickers_enabled,
            "emoji_reactions": settings.reactions_enabled,
        },
        "version": "2.0.0",
    }
