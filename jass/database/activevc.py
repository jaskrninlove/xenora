# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import activevcdb


async def set_active(chat_id: int):
    await activevcdb.update_one(
        {"_id": chat_id},
        {"$set": {"active": True}},
        upsert=True,
    )


async def remove_active(chat_id: int):
    await activevcdb.delete_one({"_id": chat_id})


async def get_active_vc_count():
    return await activevcdb.count_documents({})