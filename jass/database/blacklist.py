# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import blacklistdb


async def blacklist_chat(chat_id: int):
    await blacklistdb.update_one(
        {"_id": chat_id},
        {"$set": {"blacklisted": True}},
        upsert=True,
    )


async def is_blacklisted(chat_id: int):
    return bool(await blacklistdb.find_one({"_id": chat_id}))