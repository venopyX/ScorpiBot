import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from telegram.ext import filters
from utils import ScorpiAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ScorpiBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()

        # Command Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Message Handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_message = "Hey there! I'm Scorpibot, your friendly assistant. Let's have some fun! 🎉"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)
        logger.info(f"Sent start message to {update.effective_chat.id}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = (
            "Here's what I can do:\n"
            "- Respond to your messages with fun and engaging replies.\n"
            "- Handle commands like /start and /help.\n"
            "- Play games, share jokes, and much more!\n"
            "Just mention me in a group or chat with me privately to see my magic! ✨"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)
        logger.info(f"Sent help message to {update.effective_chat.id}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text.lower()
        chat_type = update.message.chat.type
        logger.debug(f"Received message: {user_message} in {chat_type}")

        if chat_type == "private" or chat_type == "group":
            try:
                # Make the API call
                api_response = ScorpiAPI.get_response(user_message)
                logger.debug(f"API response data: {api_response}")

                # Use the plain string response directly
                reply_text = api_response if api_response else "Sorry, I couldn't understand that. Can you try again? 🤔"

                await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)
                logger.debug(f"Sending message: '{reply_text}' to chat_id: {chat_id}")
                logger.info(f"Sent response to {update.effective_chat.id}")
            except Exception as e:
                logger.error(f"Error in message_handler: {e}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Oops! Something went wrong. 😅")
                logger.debug(f"Sending message: '{reply_text}' to chat_id: {chat_id}")

    def run(self):
        logger.info("Starting Scorpibot...")
        self.application.run_polling()
