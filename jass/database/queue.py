# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import queuedb


async def add_queue(chat_id: int, song: dict):
    await queuedb.update_one(
        {"_id": chat_id},
        {"$push": {"songs": song}},
        upsert=True,
    )


async def get_queue(chat_id: int):
    data = await queuedb.find_one({"_id": chat_id})
    return data.get("songs", []) if data else []


async def clear_queue(chat_id: int):
    await queuedb.delete_one({"_id": chat_id})