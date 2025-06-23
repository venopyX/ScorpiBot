"""Health check API endpoints for deployment monitoring."""
import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import Response as FastAPIResponse
from config import BOT_TOKEN, API_BASE_URL, API_TOKEN
from api_client import get_api_client

logger = logging.getLogger(__name__)

# Create FastAPI app for health checks
app = FastAPI(
    title="Princess Selene Bot Health API",
    description="Health monitoring endpoints for Princess Selene Telegram Bot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/", summary="API Health Check")
@app.head("/", summary="API Health Check HEAD")
async def root(request: Request):
    """Root endpoint for health check."""
    # For HEAD requests, return empty response with headers
    if request.method == "HEAD":
        return FastAPIResponse(
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Health-Status": "OK",
                "X-Service": "PrincessSeleneBot",
                "X-Version": "1.0.0",
            }
        )
    
    # For GET requests, return full JSON response
    return {
        "message": "👑 Princess Selene Bot v1.0 is running!",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "bot_type": "telegram",
        "features": {
            "multilingual_support": True,
            "ai_responses": True,
            "group_chat": True,
            "private_chat": True
        }
    }

@app.get("/health", summary="Detailed Health Check")
@app.head("/health", summary="Detailed Health Check HEAD")
async def health_check(request: Request):
    """Detailed health check endpoint."""
    try:
        # Test AI API service
        api_client = get_api_client()
        test_status = api_client.health_check()
        service_status = "healthy" if test_status else "degraded"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        service_status = "unhealthy"
    
    # Check environment variables
    config_status = "healthy" if all([BOT_TOKEN, API_BASE_URL, API_TOKEN]) else "unhealthy"
    
    # Overall status
    overall_status = "healthy" if service_status == "healthy" and config_status == "healthy" else "degraded"
    
    # For HEAD requests, return status in headers only
    if request.method == "HEAD":
        status_code = 200 if overall_status == "healthy" else 503
        return FastAPIResponse(
            status_code=status_code,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Health-Status": overall_status.upper(),
                "X-Service": "PrincessSeleneBot",
                "X-Version": "1.0.0",
                "X-AI-Status": service_status.upper(),
                "X-Config-Status": config_status.upper(),
                "X-Timestamp": str(int(time.time())),
            }
        )
    
    # For GET requests, return full JSON response
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "version": "1.0.0",
        "bot_type": "telegram",
        "services": {
            "ai_api": service_status,
            "configuration": config_status,
            "telegram_polling": "active"
        },
        "features": {
            "language_detection": "active",
            "translation": "active",
            "message_history": "active",
            "personality": "Princess Selene"
        }
    }

@app.head("/ping", summary="Simple Ping Check")
async def ping_check():
    """Simple ping endpoint for monitoring services."""
    return FastAPIResponse(
        status_code=200,
        headers={
            "Content-Type": "text/plain",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Health-Status": "OK",
            "X-Service": "PrincessSeleneBot",
            "X-Ping": "PONG",
        }
    )

@app.get("/ping", summary="Simple Ping Check GET")
async def ping_check_get():
    """Simple ping endpoint for GET requests."""
    return {
        "status": "OK",
        "message": "PONG",
        "timestamp": time.time(),
        "service": "PrincessSeleneBot",
        "bot_name": "Princess Selene"
    }

@app.get("/status", summary="Bot Status Information")
async def bot_status():
    """Get detailed bot status and configuration."""
    return {
        "bot_name": "Princess Selene",
        "personality": "Cute, flirty, and playful",
        "creator": "@pandinuse",
        "languages_supported": ["English", "Amharic", "Afan Oromo"],
        "chat_types": ["private", "group"],
        "trigger_keywords": ["princess", "selene", "how are you", "joke", "fun", "guys", "jema"],
        "features": {
            "ai_powered_responses": True,
            "multilingual_support": True,
            "message_history": True,
            "auto_translation": True,
            "context_awareness": True
        },
        "uptime": time.time(),
        "version": "1.0.0"
    }

@app.get("/metrics", summary="Bot Metrics")
async def bot_metrics():
    """Basic metrics endpoint for monitoring."""
    return {
        "service": "PrincessSeleneBot",
        "status": "running",
        "timestamp": time.time(),
        "memory_usage": "low",
        "cpu_usage": "low",
        "response_time": "fast",
        "api_health": "connected"
    }