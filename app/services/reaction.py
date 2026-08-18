"""Extracts the AI's reaction suggestion from its reply.

Per app.core.instruction.Instruction.reaction_directive(), the model is
asked to end every reply with a control line like:

    REACT: \U0001F923
    REACT: NONE

That line is a signal, not chat content - the AI decides, based on the
full conversation, whether the moment is emotional enough to react to at
all ("sometimes, only in a high mood," never on every message). This
module pulls that line out, validates the emoji against the fixed
Telegram-legal set, and returns clean reply text with the control line
removed so the user never sees it.

Fails safe: if the tag is missing, malformed, or suggests something
outside the allowed set, we simply react with nothing rather than guess.
"""
import logging
import re
from typing import Optional, Tuple

from app.core.constants import REACTION_EMOJIS, REACTION_NONE_TOKEN, REACTION_TAG_PREFIX

logger = logging.getLogger(__name__)

_TAG_PATTERN = re.compile(
    re.escape(REACTION_TAG_PREFIX) + r"\s*(\S+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_reaction(ai_reply: str) -> Tuple[str, Optional[str]]:
    """Split the reaction control line off of the AI's raw reply.

    Returns (clean_reply_text, reaction_emoji_or_None).
    """
    match = _TAG_PATTERN.search(ai_reply)
    if not match:
        return ai_reply.strip(), None

    clean_reply = ai_reply[: match.start()].strip()
    suggestion = match.group(1).strip()

    if suggestion.upper() == REACTION_NONE_TOKEN:
        return clean_reply, None

    if suggestion in REACTION_EMOJIS:
        return clean_reply, suggestion

    logger.debug("Ignoring reaction suggestion outside allowed set: %r", suggestion)
    return clean_reply, None
