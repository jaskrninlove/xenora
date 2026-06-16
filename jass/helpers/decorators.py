# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from functools import wraps
from ..config import config

def owner_only(func):
    @wraps(func)
    async def wrapper(client, message):
        if message.from_user and message.from_user.id == config.OWNER_ID:
            return await func(client, message)
        return await message.reply_text("ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ. 𐙚")
    return wrapper
