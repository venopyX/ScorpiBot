import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from utils import ScorpiAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PrincessSeleneBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()
        self.last_update_id = None  # To keep track of the last processed update

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

    async def group_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.last_update_id and update.update_id <= self.last_update_id:
            return  # Skip processing if the message is older than the last processed one

        user_message = update.message.text.lower()
        chat_type = update.message.chat.type
        user_name = update.message.from_user.first_name
        user_username = update.message.from_user.username
        message_id = update.message.message_id
        logger.debug(f"Received message from {user_name} (@{user_username}): {user_message} in {chat_type}")

        triggers = ["hi", "hello", "how are you", "love", "joke", "fun"]  

        if any(trigger in user_message for trigger in triggers) or update.message.reply_to_message:
            try:
                # Include sender's name and username with the message text
                full_message = f"{user_message} [From: {user_name} (@{user_username})]"
                
                # Make the API call
                api_response = ScorpiAPI.get_response(full_message)
                logger.debug(f"API response data: {api_response}")

                # Use the plain string response directly
                reply_text = api_response if api_response else "Sorry, I couldn't understand that. Can you try again? 🤔"

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=reply_text,
                    reply_to_message_id=message_id  # Reply to the original message
                )
                logger.info(f"Sent response to {update.effective_chat.id} in reply to message {message_id}")
            except Exception as e:
                logger.error(f"Error in group_message_handler: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Oops! Something went wrong. 😅",
                    reply_to_message_id=message_id
                )

        self.last_update_id = update.update_id  # Update the last processed update ID

    async def private_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text.lower()
        user_name = update.message.from_user.first_name
        user_username = update.message.from_user.username
        message_id = update.message.message_id
        logger.debug(f"Received private message from {user_name} (@{user_username}): {user_message}")

        try:
            # Include sender's name and username with the message text
            full_message = f"{user_message} [From: {user_name} (@{user_username})]"
            
            # Make the API call
            api_response = ScorpiAPI.get_response(full_message)
            logger.debug(f"API response data: {api_response}")

            # Use the plain string response directly
            reply_text = api_response if api_response else "Sorry, I couldn't understand that. Can you try again? 🤔"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=reply_text,
                reply_to_message_id=message_id  # Reply to the original message
            )
            logger.info(f"Sent response to {update.effective_chat.id} in reply to message {message_id}")
        except Exception as e:
            logger.error(f"Error in private_message_handler: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Oops! Something went wrong. 😅",
                reply_to_message_id=message_id
            )

    def run(self):
        logger.info("Starting Princess Selene...")
        self.application.run_polling()
