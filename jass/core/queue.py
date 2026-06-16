# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class Track:
    title: str
    url: str
    stream: str
    duration: str
    thumbnail: str
    requested_by: str

class Queue:
    def __init__(self):
        self._queue = {}

    def add(self, chat_id: int, track):
        self._queue.setdefault(chat_id, []).append(track)
        return len(self._queue[chat_id])

    def pop(self, chat_id: int):
        if chat_id not in self._queue:
            return None

        if not self._queue[chat_id]:
            return None

        return self._queue[chat_id].pop(0)

    def list(self, chat_id: int):
        return self._queue.get(chat_id, [])

    def clear(self, chat_id: int):
        self._queue.pop(chat_id, None)


queue = Queue()