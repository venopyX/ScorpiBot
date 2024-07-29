import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from utils import ScorpiAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define your triggers here
TRIGGER_KEYWORDS = ["hello", "help", "hi"]  # Add more keywords as needed

class ScorpiBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()

        # Command Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Message Handlers
        self.application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self.message_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, self.message_handler))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_message = "Hey there! I'm Scorpibot, your friendly assistant. Let's have some fun! 🎉"
        await context.bot.reply_to_message(chat_id=update.effective_chat.id, text=start_message)
        logger.info(f"Sent start message to {update.effective_chat.id}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = (
            "Here's what I can do:\n"
            "- Respond to your messages with fun and engaging replies.\n"
            "- Handle commands like /start and /help.\n"
            "- Play games, share jokes, and much more!\n"
            "Just mention me in a group or chat with me privately to see my magic! ✨"
        )
        await context.bot.reply_to_message(chat_id=update.effective_chat.id, text=help_message)
        logger.info(f"Sent help message to {update.effective_chat.id}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text.lower()
        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        chat_type = update.message.chat.type
        from_user_id = update.message.from_user.id
        bot_username = context.bot.username

        logger.debug(f"Received message: '{user_message}' in chat_id: {chat_id} of type: {chat_type}")

        # Check if the message contains any trigger keywords
        if any(keyword in user_message for keyword in TRIGGER_KEYWORDS):
            reply_text = "I see a trigger word! 😎"

        # Check if the bot is mentioned
        elif f"@{bot_username}" in user_message:
            reply_text = "Did you call me? 😏"

        # Check if the message is a reply to one of the bot's messages
        elif update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            reply_text = "Replying to my message, I see! 😆"

        else:
            logger.debug("Message does not match any triggers.")
            return  # Do nothing if none of the triggers are matched

        try:
            # Make the API call only if a trigger is matched
            api_response = ScorpiAPI.get_response(user_message)
            logger.debug(f"API response data: {api_response}")

            # Use the plain string response directly
            reply_text = api_response if api_response else reply_text

            await context.bot.send_message(chat_id=chat_id, text=reply_text, reply_to_message_id=message_id)
            logger.info(f"Sent response to chat_id: {chat_id}, in reply to message_id: {message_id}")
        except Exception as e:
            logger.error(f"Error in message_handler: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Oops! Something went wrong. 😅", reply_to_message_id=message_id)

    def run(self):
        logger.info("Starting Scorpibot...")
        self.application.run_polling()
