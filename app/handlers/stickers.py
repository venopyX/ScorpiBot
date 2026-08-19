"""Handles incoming stickers by replying with another random sticker from
the same pack the user sent."""
import logging

from telegram import Update
from telegram.ext import ContextTypes, filters

from app.services.stickers import get_sticker_service

logger = logging.getLogger(__name__)

# Shown when the user sends a one-off sticker that isn't part of a named
# pack, so we have nothing to draw a "reply sticker" from.
_NO_PACK_FALLBACK = "Cute sticker, but it's not from a pack I can dig through! \U0001F9F5"


class ShouldRespondSticker(filters.MessageFilter):
    """Only respond to stickers that are sent directly (DM) or replied to the bot."""

    def filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        message = update.message
        if not message or not message.sticker:
            return False

        # Always respond in private chats (DMs)
        chat_type = message.chat.type
        if chat_type == "private":
            return True

        # In groups, only respond if the sticker is a reply to the bot
        if chat_type in ("group", "supergroup"):
            replied = message.reply_to_message
            if replied and replied.from_user and replied.from_user.id == context.bot.id:
                return True

        return False


should_respond_sticker = ShouldRespondSticker()


async def sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.sticker:
        return

    sticker = message.sticker
    set_name = sticker.set_name

    if not set_name:
        logger.debug("Sticker from %s has no pack, skipping reply sticker", message.from_user.id)
        return

    service = get_sticker_service()
    reply_file_id = await service.get_random_sticker(
        context.bot, set_name, exclude_file_id=sticker.file_id
    )

    if not reply_file_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=_NO_PACK_FALLBACK,
            reply_to_message_id=message.message_id,
        )
        return

    await context.bot.send_sticker(
        chat_id=update.effective_chat.id,
        sticker=reply_file_id,
        reply_to_message_id=message.message_id,
    )
    logger.info("Replied with sticker from pack '%s' to chat %s", set_name, update.effective_chat.id)
