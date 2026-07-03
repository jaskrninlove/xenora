# ==========================================================
# JassMusic - Queue Manager
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

from dataclasses import dataclass
from typing import Any


@dataclass
class Track:
    title: str
    url: str
    stream: str | None = None
    duration: int | str = 0
    thumbnail: str | None = None
    requested_by: str | None = None
    webpage_url: str | None = None
    is_video: bool = False


class Queue:
    def __init__(self):
        self._queue: dict[int, list[Any]] = {}

    def add(self, chat_id: int, track: Any) -> int:
        self._queue.setdefault(chat_id, []).append(track)
        return len(self._queue[chat_id])

    def pop(self, chat_id: int):
        items = self._queue.get(chat_id)

        if not items:
            return None

        track = items.pop(0)

        if not items:
            self._queue.pop(chat_id, None)

        return track

    def list(self, chat_id: int) -> list[Any]:
        return list(self._queue.get(chat_id, []))

    def clear(self, chat_id: int):
        self._queue.pop(chat_id, None)

    def count(self, chat_id: int) -> int:
        return len(self._queue.get(chat_id, []))

    def has_items(self, chat_id: int) -> bool:
        return bool(self._queue.get(chat_id))


queue = Queue()