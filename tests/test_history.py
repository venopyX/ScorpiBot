"""Tests for per-user message history bookkeeping."""
from app.services.history import MessageHistory


def test_add_and_get_history():
    history = MessageHistory()
    history.add_message(1, "hello")
    history.add_message(1, "world")
    assert history.get_history(1) == "hello world"


def test_history_is_per_user():
    history = MessageHistory()
    history.add_message(1, "from user 1")
    history.add_message(2, "from user 2")
    assert history.get_history(1) == "from user 1"
    assert history.get_history(2) == "from user 2"


def test_unknown_user_returns_empty_string():
    history = MessageHistory()
    assert history.get_history(999) == ""


def test_char_limit_trims_oldest_messages():
    history = MessageHistory()
    # Each message is 200 chars; limit is 1000, so only the last ~5 survive.
    for i in range(10):
        history.add_message(1, f"msg{i}" + "x" * 195)
    assert len(history.get_history(1)) <= 1000
