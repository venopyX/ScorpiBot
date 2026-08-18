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

BUG #1 (fixed): the first version required at least one non-space
character after "REACT:" (`\\S+`). When the model wrote a bare "REACT:"
with nothing after it, the regex simply didn't match, so the whole line
sailed through untouched into the translated reply. Fixed by matching the
entire last line and treating an empty suggestion the same as NONE.

BUG #2 (fixed): the follow-up version required the suggestion to be an
*exact* match against one of the allowed emoji strings
(`suggestion in REACTION_EMOJIS`). In practice the model doesn't always
produce a byte-for-byte clean emoji - it might add a trailing period, a
parenthetical, extra whitespace, or wrap the emoji in a short phrase (e.g.
"REACT: 🔥 lol" or "REACT: (🔥)"). Any of that made the exact-match check
fail and reactions silently stopped firing at all. Fixed by falling back
to a substring search for a known emoji anywhere in the suggestion once an
exact match fails, so formatting noise around the emoji doesn't matter -
only its presence does.
"""
import logging
import re
from typing import Optional, Tuple

from app.core.constants import REACTION_EMOJIS, REACTION_NONE_TOKEN

logger = logging.getLogger(__name__)

# Matches an entire line that starts with "react", optionally followed by
# a colon, optionally followed by a suggestion - colon and suggestion are
# both optional so a bare "REACT:" or even bare "REACT" is still recognized
# and stripped, rather than leaking through untouched.
_REACT_LINE = re.compile(r"^\s*react\s*:?\s*(.*?)\s*$", re.IGNORECASE)

# Longest first so a compound emoji like "❤️‍🔥" is matched whole rather
# than accidentally matching a shorter emoji that happens to be a prefix
# of its codepoint sequence.
_EMOJIS_BY_LENGTH = tuple(sorted(REACTION_EMOJIS, key=len, reverse=True))


def _find_allowed_emoji(suggestion: str) -> Optional[str]:
    """Find a known-good reaction emoji anywhere in `suggestion`.

    Tries an exact match first (the common, clean case), then falls back
    to a substring search so incidental formatting around the emoji -
    trailing punctuation, a stray word, extra whitespace - doesn't cause
    a perfectly good suggestion to be thrown away.
    """
    if suggestion in REACTION_EMOJIS:
        return suggestion

    for emoji in _EMOJIS_BY_LENGTH:
        if emoji in suggestion:
            return emoji

    return None


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

    emoji = _find_allowed_emoji(suggestion)
    if emoji is None:
        logger.debug("Ignoring reaction suggestion outside allowed set: %r", suggestion)
    return clean_reply, emoji
