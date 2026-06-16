# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import chatsdb


async def add_chat(chat_id: int):
    if not await chatsdb.find_one({"_id": chat_id}):
        await chatsdb.insert_one({"_id": chat_id})


async def get_chats_count():
    return await chatsdb.count_documents({})