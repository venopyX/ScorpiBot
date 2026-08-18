"""Bot-wide constants."""

TRIGGER_KEYWORDS = ["princess", "selene", "how are you", "joke", "fun", "guys", "jema"]

MESSAGE_HISTORY_CHAR_LIMIT = 1000
MESSAGE_HISTORY_TIME_LIMIT_SECONDS = 3600  # 1 hour

FALLBACK_REPLY = "Oops! Sorry what did u say? \U0001F61C"
ERROR_REPLY = "Oops! Something went wrong. \U0001F605"

# How long a sticker pack's contents are cached before we re-fetch it from Telegram.
STICKER_PACK_CACHE_SECONDS = 3600

# The only emojis the bot is allowed to react with. Deliberately small and
# high-signal - these are meant to be used sparingly, only when the AI
# judges the mood genuinely calls for one. Every value here must also exist
# in telegram.constants.ReactionEmoji (Telegram bots can only react with a
# fixed allow-list); tests/test_reaction.py checks that.
REACTION_EMOJIS = (
    "\u2764\uFE0F\u200D\U0001F525",  # ❤️‍🔥
    "\U0001F48B",  # 💋
    "\U0001F923",  # 🤣
    "\U0001F970",  # 🥰
    "\U0001F60D",  # 😍
    "\U0001F525",  # 🔥
    "\U0001F62D",  # 😭
    "\U0001F494",  # 💔
    "\U0001F621",  # 😡
)

# The exact control-line format the AI is asked to append to its replies.
# See app.core.instruction.Instruction.reaction_directive().
REACTION_TAG_PREFIX = "REACT:"
REACTION_NONE_TOKEN = "NONE"
