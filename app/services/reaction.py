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
removed so the user never sees it - and, just as importantly, so it never
reaches the translator (which will happily translate the literal word
"React" into a phrase in the target language if we let it).

BUG THIS FIXES: the first version required at least one non-space
character after "REACT:" (`\\S+`). When the model wrote a bare "REACT:"
with nothing after it - which it does sometimes, especially when it means
to say "no reaction" - the regex simply didn't match, so the whole line
(and only the whole line) sailed through untouched into the translated
reply, e.g. "REACT:" or its translated form "\u121D\u120B\u123D \u12ED\u1235\u1327". This
version matches on the *last line itself* starting with "react" and
requires nothing to follow it, so a blank suggestion is treated the same
as an explicit NONE.
"""
import logging
import re

from app.core.constants import REACTION_EMOJIS, REACTION_NONE_TOKEN
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Matches an entire line that starts with "react", optionally followed by
# a colon, optionally followed by a suggestion - colon and suggestion are
# both optional so a bare "REACT:" or even bare "REACT" is still recognized
# and stripped, rather than leaking through untouched.
_REACT_LINE = re.compile(r"^\s*react\s*:?\s*(.*?)\s*$", re.IGNORECASE)


def extract_reaction(ai_reply: str) -> Tuple[str, Optional[str]]:
    """Split the reaction control line off of the AI's raw reply.

    Looks only at the last non-empty line, since that's where the
    directive asks the model to put it. Returns
    (clean_reply_text, reaction_emoji_or_None).
    """
    text = ai_reply.rstrip()
    if not text:
        return ai_reply.strip(), None

    lines = text.split("\n")
    last_line = lines[-1]

    match = _REACT_LINE.match(last_line)
    if not match:
        # Model didn't include a recognizable control line at all - fail
        # safe: show the reply as-is, react to nothing.
        return text.strip(), None

    clean_reply = "\n".join(lines[:-1]).strip()
    suggestion = match.group(1).strip()

    if not suggestion or suggestion.upper() == REACTION_NONE_TOKEN:
        return clean_reply, None

    if suggestion in REACTION_EMOJIS:
        return clean_reply, suggestion

    logger.debug("Ignoring reaction suggestion outside allowed set: %r", suggestion)
    return clean_reply, None
