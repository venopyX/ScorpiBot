"""Looks up sticker packs and picks a random sticker to reply with."""
import logging
import random
import time
from typing import Dict, List, Optional, Tuple

from telegram import Bot

from app.core.constants import STICKER_PACK_CACHE_SECONDS

logger = logging.getLogger(__name__)


class StickerService:
    """Fetches a sticker pack's contents (with caching) and picks a random one.

    Telegram identifies a sticker's pack via `sticker.set_name` - stickers a
    user sends that aren't part of a named pack (one-off custom stickers)
    have `set_name is None`, and callers should handle that case separately.
    """

    def __init__(self) -> None:
        # set_name -> (fetched_at, [file_id, ...])
        self._cache: Dict[str, Tuple[float, List[str]]] = {}

    async def get_random_sticker(
        self, bot: Bot, set_name: str, exclude_file_id: Optional[str] = None
    ) -> Optional[str]:
        """Return a random sticker file_id from `set_name`, or None if unavailable."""
        file_ids = await self._get_pack_file_ids(bot, set_name)
        if not file_ids:
            return None

        choices = [fid for fid in file_ids if fid != exclude_file_id] or file_ids
        return random.choice(choices)

    async def _get_pack_file_ids(self, bot: Bot, set_name: str) -> List[str]:
        cached = self._cache.get(set_name)
        now = time.time()
        if cached and now - cached[0] < STICKER_PACK_CACHE_SECONDS:
            return cached[1]

        try:
            sticker_set = await bot.get_sticker_set(set_name)
        except Exception as exc:
            logger.warning("Could not fetch sticker set '%s': %s", set_name, exc)
            return cached[1] if cached else []

        file_ids = [sticker.file_id for sticker in sticker_set.stickers]
        self._cache[set_name] = (now, file_ids)
        return file_ids


_service: Optional[StickerService] = None


def get_sticker_service() -> StickerService:
    global _service
    if _service is None:
        _service = StickerService()
    return _service
