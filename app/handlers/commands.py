"""Simple slash-command handlers."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

START_MESSAGE = "Hey \U0001F618\U0001F602"

HELP_MESSAGE = (
    "Here's what I can do:\n"
    "- Chat with you in a fun and flirty way.\n"
    "- Reply with a sticker when you send me one from a pack.\n"
    "- React with an emoji when your message feels funny, sad, or sweet.\n"
    "Just mention me in a group or chat with me privately to see my magic! \u2728"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=START_MESSAGE)
    logger.info("Start command sent to %s", update.effective_chat.id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=HELP_MESSAGE)
    logger.info("Help command sent to %s", update.effective_chat.id)
