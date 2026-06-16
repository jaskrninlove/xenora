# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from pyrogram import filters, StopPropagation
from pyrogram.handlers import MessageHandler

from ..core.database import db
from ..config import config


def register(app, call):

    async def gate(client, message):
        if not message.from_user:
            return

        user_id = message.from_user.id

        if user_id == config.OWNER_ID:
            return

        if await db.is_gbanned(user_id):
            doc = await db.get_gban(user_id)
            reason = doc.get("reason", "No reason provided") if doc else "No reason provided"

            await message.reply_text(
                f"""<blockquote><b>🔨 Access Denied — Global Ban</b></blockquote>

❖ <b>Reason :</b> {reason}

<blockquote>Contact the bot owner if this is a mistake.</blockquote>"""
            )
            raise StopPropagation

        if await db.is_maintenance():
            if message.text and message.text.startswith("/"):
                await message.reply_text(
                    """<blockquote><b>🔧 Under Maintenance</b></blockquote>

The bot is currently undergoing maintenance and will be back shortly.

<blockquote>♫ Thank you for your patience.</blockquote>"""
                )
                raise StopPropagation

    app.add_handler(MessageHandler(gate, filters.all), group=-1)