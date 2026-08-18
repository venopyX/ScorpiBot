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


def test_all_reaction_emojis_are_telegram_legal():
    allowed = {e.value for e in ReactionEmoji}
    for emoji in REACTION_EMOJIS:
        assert emoji in allowed, f"{emoji!r} is not a Telegram-legal reaction emoji"
