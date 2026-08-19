"""Application entrypoint: builds the Telegram bot, registers handlers, and
runs the health-check API alongside it."""
import logging
import sys
import threading

import uvicorn
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from app.config import settings
from app.handlers.commands import help_command, start_command
from app.handlers.messages import MessageProcessor
from app.handlers.stickers import should_respond_sticker, sticker_handler
from app.health.api import app as health_app

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class PrincessSeleneBot:
    """Owns the Telegram Application and wires up all handlers."""

    def __init__(self, token: str) -> None:
        self.application = ApplicationBuilder().token(token).build()
        self.message_processor = MessageProcessor()
        self._register_handlers()
        logger.info("Bot initialized successfully")

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))

        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self._group_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, self._private_message)
        )

        if settings.stickers_enabled:
            # Only handle stickers sent directly to bot (DM) or replied to bot
            sticker_filter = filters.Sticker.ALL & filters.create(should_respond_sticker)
            self.application.add_handler(MessageHandler(sticker_filter, sticker_handler))

        logger.info("Handlers registered successfully")

    async def _group_message(self, update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self.message_processor.should_respond_in_group(update, context):
            await self.message_processor.process_message(update, context, "group")

    async def _private_message(self, update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.message_processor.process_message(update, context, "private")

    def run_polling(self) -> None:
        logger.info("Starting Princess Selene Bot polling...")
        try:
            self.application.run_polling(drop_pending_updates=True)
        except Exception as exc:
            logger.error("Bot polling crashed: %s", exc)
            raise


def run_health_api() -> None:
    logger.info("Starting health API server on port %s...", settings.health_port)
    uvicorn.run(health_app, host="0.0.0.0", port=settings.health_port, log_level="info", access_log=True)


def main() -> None:
    try:
        settings.validate()

        health_thread = threading.Thread(target=run_health_api, daemon=True)
        health_thread.start()
        logger.info("Health API started in background thread")

        bot = PrincessSeleneBot(settings.bot_token)
        bot.run_polling()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as exc:
        logger.error("Failed to start bot: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
