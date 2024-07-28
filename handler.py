# handler.py
from pyrogram import Client, filters
from utils import ScorpiAPI
import config

class ScorpiBot:
    def __init__(self):
        self.app = Client("scorpibot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)
        self.app.add_handler(self.message_handler)

    async def message_handler(self, client, message):
        user_message = message.text.lower()
        response = ScorpiAPI.get_response(user_message)
        await message.reply_text(response)

    def run(self):
        self.app.run()
