"""Short-lived per-user chat history, used to give the AI conversational context."""
import time
from collections import deque
from typing import Deque, Dict, Tuple

from app.core.constants import (
    MESSAGE_HISTORY_CHAR_LIMIT,
    MESSAGE_HISTORY_TIME_LIMIT_SECONDS,
)


class MessageHistory:
    """Keeps each user's recent messages, bounded by both age and total length."""

    def __init__(self) -> None:
        self._histories: Dict[int, Deque[Tuple[str, float]]] = {}

    def add_message(self, user_id: int, message: str) -> None:
        history = self._histories.setdefault(user_id, deque())
        now = time.time()
        history.append((message, now))
        self._trim(user_id, now)

    def get_history(self, user_id: int) -> str:
        history = self._histories.get(user_id)
        if not history:
            return ""
        return " ".join(message for message, _ in history)

    def _trim(self, user_id: int, now: float) -> None:
        history = self._histories[user_id]

        while history and now - history[0][1] > MESSAGE_HISTORY_TIME_LIMIT_SECONDS:
            history.popleft()

        total_chars = sum(len(message) for message, _ in history)
        while total_chars > MESSAGE_HISTORY_CHAR_LIMIT and history:
            removed_message, _ = history.popleft()
            total_chars -= len(removed_message)
