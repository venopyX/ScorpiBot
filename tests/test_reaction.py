"""Tests for parsing the AI's own reaction suggestion out of its reply."""
from telegram.constants import ReactionEmoji

from app.core.constants import REACTION_EMOJIS
from app.services.reaction import extract_reaction


def test_extracts_valid_reaction_and_strips_tag():
    reply = "Kiss me right now honey, missing those lips \U0001F48B\nREACT: \U0001F48B"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F48B"
    assert "REACT" not in clean


def test_none_token_means_no_reaction():
    reply = "How was your day today\nREACT: NONE"
    clean, emoji = extract_reaction(reply)
    assert emoji is None
    assert clean == "How was your day today"


def test_bare_react_with_nothing_after_it_is_treated_as_no_reaction():
    """Regression test: the model sometimes writes a bare "REACT:" with no
    emoji after it. The old regex required \\S+ after the colon and simply
    didn't match, so the literal line "REACT:" (and its Amharic
    mistranslation "\u121D\u120B\u123D \u12ED\u1235\u1327") leaked straight into what the
    user saw. This must be stripped and treated as no reaction."""
    reply = "You are making me blush with that sweet message, love\n\nREACT:"
    clean, emoji = extract_reaction(reply)
    assert emoji is None
    assert "REACT" not in clean
    assert clean == "You are making me blush with that sweet message, love"


def test_bare_react_with_trailing_whitespace_only():
    reply = "Sweet dreams\nREACT:   "
    clean, emoji = extract_reaction(reply)
    assert emoji is None
    assert "REACT" not in clean


def test_react_without_colon_is_still_recognized():
    reply = "So funny\nREACT \U0001F923"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F923"
    assert "REACT" not in clean


def test_missing_tag_fails_safe_to_no_reaction():
    reply = "Just a plain reply with no control line at all"
    clean, emoji = extract_reaction(reply)
    assert emoji is None
    assert clean == reply


def test_emoji_outside_allowed_set_is_ignored():
    reply = "Nice one\nREACT: \U0001F44D"  # 👍 not in our curated set
    clean, emoji = extract_reaction(reply)
    assert emoji is None
    assert "REACT" not in clean


def test_tag_is_case_insensitive():
    reply = "So funny\nreact: \U0001F923"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F923"


def test_emoji_with_trailing_punctuation_still_matches():
    """Regression test: an exact-match-only check silently kills reactions
    the moment the model adds any stray character around the emoji, which
    is common in the wild ("REACT: 🔥." or "REACT: 🔥!")."""
    reply = "That is so hot\nREACT: \U0001F525."
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F525"


def test_emoji_wrapped_in_extra_words_still_matches():
    reply = "I am so proud of you\nREACT: I'll go with \U0001F525 for this one"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F525"


def test_emoji_with_surrounding_whitespace_or_parens():
    reply = "Aww\nREACT: (\U0001F970)"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\U0001F970"


def test_compound_emoji_not_shadowed_by_shorter_prefix_emoji():
    """❤️‍🔥 shares codepoints with plain ❤ - the longer compound emoji
    must win when it's actually what's present."""
    reply = "You are so bold\nREACT: \u2764\uFE0F\u200D\U0001F525"
    clean, emoji = extract_reaction(reply)
    assert emoji == "\u2764\uFE0F\u200D\U0001F525"


def test_all_reaction_emojis_are_telegram_legal():
    allowed = {e.value for e in ReactionEmoji}
    for emoji in REACTION_EMOJIS:
        assert emoji in allowed, f"{emoji!r} is not a Telegram-legal reaction emoji"
