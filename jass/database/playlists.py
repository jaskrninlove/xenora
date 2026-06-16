# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import playlistdb


async def save_playlist(user_id: int, tracks: list):
    await playlistdb.update_one(
        {"_id": user_id},
        {"$set": {"tracks": tracks}},
        upsert=True,
    )


async def get_playlist(user_id: int):
    data = await playlistdb.find_one({"_id": user_id})
    return data.get("tracks", []) if data else []