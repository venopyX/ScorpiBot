import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from utils import ScorpiAPI
from text_processor import TextManager  # Assuming your TextManager and related classes are in a file named text_processor.py

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PrincessSeleneBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()
        self.last_update_id = None  # To keep track of the last processed update
        self.text_manager = TextManager()  # Initialize TextManager

        # Command Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Message Handlers
        self.application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self.group_message_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, self.private_message_handler))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_message = (
            "Hey there, cutie! I'm Princess Selene, your flirty, fun, and oh-so-cute chat buddy. 😘 Let's get this party started with some sweet talk and lots of laughs! 😂"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)
        logger.info(f"Sent start message to {update.effective_chat.id}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = (
            "Here's what I can do:\n"
            "- Chat with you in a fun and flirty way.\n"
            "- Engage in playful and warm conversations with you!\n"
            "Just mention me in a group or chat with me privately to see my magic! ✨"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)
        logger.info(f"Sent help message to {update.effective_chat.id}")

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_type: str):
        if self.last_update_id and update.update_id <= self.last_update_id:
            return  # Skip processing if the message is older than the last processed one

        if not update.message:
            return  # Skip updates that are not messages

        user_message = update.message.text
        user_name = update.message.from_user.first_name
        user_username = update.message.from_user.username
        message_id = update.message.message_id
        logger.debug(f"Received message from {user_name} (@{user_username}): {user_message} in {chat_type}")

        try:
            # Detect and translate to English
            translated_message, original_language_code = self.text_manager.detect_and_translate_to_english(user_message)

            # Make the API call
            api_response = ScorpiAPI.get_response(translated_message)
            logger.debug(f"API response data: {api_response}")

            # Translate the response back to the original language
            reply_text = self.text_manager.translate_from_english(api_response, original_language_code)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=reply_text,
                reply_to_message_id=message_id  # Reply to the original message
            )
            logger.info(f"Sent response to {update.effective_chat.id} in reply to message {message_id}")
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Oops! Something went wrong. 😅",
                reply_to_message_id=message_id
            )

        self.last_update_id = update.update_id  # Update the last processed update ID

    async def group_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.process_message(update, context, "group")

    async def private_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.process_message(update, context, "private")

    def run(self):
        logger.info("Starting Princess Selene...")
        self.application.run_polling()
