"""Message processing and handling logic."""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from models import MessageHistory, TRIGGER_KEYWORDS
from text_processor import TextManager
from api_client import get_api_client

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Handles message processing and response generation."""
    
    def __init__(self):
        self.message_history = MessageHistory()
        self.text_manager = TextManager()
        self.api_client = get_api_client()
        self.last_update_id: Optional[int] = None
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_type: str) -> None:
        """Process incoming message and generate response."""
        if not self._should_process_update(update):
            return
        
        if not update.message or not update.message.text:
            return
        
        user_info = self._extract_user_info(update)
        logger.debug(f"Processing message from {user_info['name']} in {chat_type}")
        
        try:
            await self._handle_message(update, context, user_info)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error_response(update, context)
        
        self.last_update_id = update.update_id
    
    def should_respond_in_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if bot should respond to group message."""
        if not update.message or not update.message.text:
            return False
        
        message_text = update.message.text.lower()
        bot_username = context.bot.username
        
        return (
            any(keyword in message_text for keyword in TRIGGER_KEYWORDS) or
            f"@{bot_username}" in message_text or
            (update.message.reply_to_message and 
             update.message.reply_to_message.from_user.id == context.bot.id)
        )
    
    def _should_process_update(self, update: Update) -> bool:
        """Check if update should be processed."""
        return not (self.last_update_id and update.update_id <= self.last_update_id)
    
    def _extract_user_info(self, update: Update) -> dict:
        """Extract user information from update."""
        user = update.message.from_user
        return {
            'id': user.id,
            'name': user.first_name,
            'username': user.username,
            'message': update.message.text,
            'message_id': update.message.message_id
        }
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_info: dict) -> None:
        """Handle message processing and response."""
        self.message_history.add_message(user_info['id'], user_info['message'])
        
        full_history = self.message_history.get_history(user_info['id'])
        translated_history, history_lang = self.text_manager.detect_and_translate_to_english(full_history)
        translated_message, _ = self.text_manager.detect_and_translate_to_english(user_info['message'])
        
        final_message = self._prepare_final_message(update, user_info, translated_message)
        api_input = f"Our Last Chat(used for to remember): {translated_history}\n\nMy new Message: {final_message}"
        
        api_response = self.api_client.get_response(api_input)
        reply_text = self.text_manager.translate_from_english(api_response, history_lang)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_text,
            reply_to_message_id=user_info['message_id']
        )
        
        logger.info(f"Sent response to {update.effective_chat.id}")
    
    def _prepare_final_message(self, update: Update, user_info: dict, translated_message: str) -> str:
        """Prepare final message with user context and reply info."""
        message = f"User {user_info['name']} (@{user_info['username']}, ID: {user_info['id']}): {translated_message}"
        
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user
            reply_info = f" (Reply from {replied_user.first_name} (@{replied_user.username}), ID: {replied_user.id})"
            message = message.replace(f": {translated_message}", f": {translated_message}{reply_info}")
        
        return message
    
    async def _send_error_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send error response to user."""
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Oops! Something went wrong. 😅",
            reply_to_message_id=update.message.message_id
        )