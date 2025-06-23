"""Data models and constants."""
from dataclasses import dataclass
from typing import Tuple, Deque
import time
from collections import deque

TRIGGER_KEYWORDS = ["princess", "selene", "how are you", "joke", "fun", "guys", "jema"]
MESSAGE_HISTORY_LIMIT = 1000
MESSAGE_HISTORY_TIME_LIMIT = 3600  # 1 hour in seconds

@dataclass
class MessageHistory:
    """Manages user message history with time and character limits."""
    
    def __init__(self):
        self.histories = {}
    
    def add_message(self, user_id: int, message: str) -> None:
        """Add message to user history with cleanup."""
        current_time = time.time()
        
        if user_id not in self.histories:
            self.histories[user_id] = deque()
        
        self.histories[user_id].append((message, current_time))
        self._cleanup_history(user_id, current_time)
    
    def get_history(self, user_id: int) -> str:
        """Get concatenated message history for user."""
        if user_id not in self.histories:
            return ""
        return ' '.join(msg[0] for msg in self.histories[user_id])
    
    def _cleanup_history(self, user_id: int, current_time: float) -> None:
        """Remove old messages based on time and character limits."""
        history = self.histories[user_id]
        
        # Remove messages older than time limit
        while history and current_time - history[0][1] > MESSAGE_HISTORY_TIME_LIMIT:
            history.popleft()
        
        # Remove old messages if character count exceeds limit
        total_chars = sum(len(msg[0]) for msg in history)
        while total_chars > MESSAGE_HISTORY_LIMIT and history:
            removed_message = history.popleft()
            total_chars -= len(removed_message[0])