# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .mongo import usersdb


async def add_user(user_id: int):
    if not await usersdb.find_one({"_id": user_id}):
        await usersdb.insert_one({"_id": user_id})


async def get_users_count():
    return await usersdb.count_documents({})