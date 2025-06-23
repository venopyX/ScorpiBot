"""Main bot application with FastAPI health endpoints."""
import asyncio
import logging
import sys
import threading
import uvicorn
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN
from message_handler import MessageProcessor
from health_api import app as health_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PrincessSeleneBot:
    """Main bot class handling Telegram interactions."""
    
    def __init__(self, token: str):
        if not token:
            raise ValueError("BOT_TOKEN is required")
        
        self.application = ApplicationBuilder().token(token).build()
        self.message_processor = MessageProcessor()
        self._register_handlers()
        logger.info("Bot initialized successfully")
    
    def _register_handlers(self) -> None:
        """Register command and message handlers."""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self.group_message_handler)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, self.private_message_handler)
        )
        logger.info("Handlers registered successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        message = "Hey there, cutie! I'm Princess Selene, your flirty, fun, and oh-so-cute chat buddy. 😘😂"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        logger.info(f"Start command sent to {update.effective_chat.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        message = (
            "Here's what I can do:\n"
            "- Chat with you in a fun and flirty way.\n"
            "- Engage in playful and warm conversations with you!\n"
            "Just mention me in a group or chat with me privately to see my magic! ✨"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        logger.info(f"Help command sent to {update.effective_chat.id}")
    
    async def group_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle group messages."""
        if self.message_processor.should_respond_in_group(update, context):
            await self.message_processor.process_message(update, context, "group")
    
    async def private_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle private messages."""
        await self.message_processor.process_message(update, context, "private")
    
    def run_polling(self) -> None:
        """Start the bot polling."""
        logger.info("Starting Princess Selene Bot polling...")
        try:
            self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Bot polling crashed: {e}")
            raise

def run_health_api():
    """Run FastAPI health check server."""
    logger.info("Starting health API server on port 8000...")
    uvicorn.run(
        health_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

def main():
    """Main function to run both bot and health API."""
    try:
        # Start health API in a separate thread
        health_thread = threading.Thread(target=run_health_api, daemon=True)
        health_thread.start()
        logger.info("Health API started in background thread")
        
        # Start bot polling in main thread
        bot = PrincessSeleneBot(BOT_TOKEN)
        bot.run_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()