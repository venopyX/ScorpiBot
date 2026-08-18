"""Text message handling: history tracking, translation, AI reply, reactions."""
import logging
from typing import Optional, TypedDict

from telegram import ReactionTypeEmoji, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.config import settings
from app.core.constants import ERROR_REPLY, TRIGGER_KEYWORDS
from app.services.ai_client import get_ai_client
from app.services.history import MessageHistory
from app.services.reaction import extract_reaction
from app.services.translator import TranslationService

logger = logging.getLogger(__name__)


class UserInfo(TypedDict):
    id: int
    name: str
    username: Optional[str]
    message: str
    message_id: int


class MessageProcessor:
    """Coordinates history, translation, the AI client, and reactions for
    every incoming text message."""

    def __init__(self) -> None:
        self.history = MessageHistory()
        self.translator = TranslationService()
        self.ai_client = get_ai_client()
        self._last_update_id: Optional[int] = None

    def should_respond_in_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Decide whether a group message should get the full AI treatment."""
        if not update.message or not update.message.text:
            return False

        text = update.message.text.lower()
        bot_username = context.bot.username

        return (
            any(keyword in text for keyword in TRIGGER_KEYWORDS)
            or f"@{bot_username}" in text
            or bool(
                update.message.reply_to_message
                and update.message.reply_to_message.from_user
                and update.message.reply_to_message.from_user.id == context.bot.id
            )
        )

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_type: str) -> None:
        if not self._is_new_update(update) or not update.message or not update.message.text:
            return

        user_info = self._extract_user_info(update)
        logger.debug("Processing message from %s in %s", user_info["name"], chat_type)

        try:
            await self._reply(update, context, user_info)
        except Exception as exc:
            logger.error("Error processing message: %s", exc)
            await self._send_error(update, context)

        self._last_update_id = update.update_id

    def _is_new_update(self, update: Update) -> bool:
        return not (self._last_update_id and update.update_id <= self._last_update_id)

    def _extract_user_info(self, update: Update) -> UserInfo:
        user = update.message.from_user
        return {
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
            "message": update.message.text,
            "message_id": update.message.message_id,
        }

    async def _apply_reaction(self, update: Update, context: ContextTypes.DEFAULT_TYPE, emoji: str) -> None:
        """Set a native Telegram reaction on the user's message. Best-effort:
        never let a reaction failure affect the actual chat reply."""
        try:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji(emoji)],
            )
            logger.debug("Reacted with %s to message %s", emoji, update.message.message_id)
        except BadRequest as exc:
            # Can fail for reasons that don't matter to the user (message
            # too old, chat doesn't allow reactions, etc).
            logger.debug("Could not set reaction: %s", exc)
        except Exception as exc:
            logger.warning("Unexpected error setting reaction: %s", exc)

    async def _reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_info: UserInfo) -> None:
        self.history.add_message(user_info["id"], user_info["message"])

        history_text = self.history.get_history(user_info["id"])
        translated_history, history_lang = self.translator.to_english(history_text)
        translated_message, _ = self.translator.to_english(user_info["message"])

        final_message = self._build_prompt_message(update, user_info, translated_message)
        prompt = f"Our Last Chat(used for to remember): {translated_history}\n\nMy new Message: {final_message}"

        ai_reply = self.ai_client.get_response(prompt)

        # The AI appends a hidden "REACT: <emoji-or-NONE>" control line to
        # its own reply (see Instruction.reaction_directive) - pull that off
        # before translating so it's never shown to the user and never run
        # through the translator.
        clean_reply, reaction_emoji = extract_reaction(ai_reply)

        reply_text = self.translator.from_english(clean_reply, history_lang)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_text,
            reply_to_message_id=user_info["message_id"],
        )
        logger.info("Sent response to %s", update.effective_chat.id)

        if settings.reactions_enabled and reaction_emoji:
            await self._apply_reaction(update, context, reaction_emoji)

    def _build_prompt_message(self, update: Update, user_info: UserInfo, translated_message: str) -> str:
        message = f"User {user_info['name']} (@{user_info['username']}, ID: {user_info['id']}): {translated_message}"

        replied = update.message.reply_to_message
        if replied and replied.from_user:
            reply_info = f" (Reply from {replied.from_user.first_name} (@{replied.from_user.username}), ID: {replied.from_user.id})"
            message += reply_info

        return message

    async def _send_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=ERROR_REPLY,
            reply_to_message_id=update.message.message_id,
        )
