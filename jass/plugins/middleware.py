# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

from pyrogram import filters, StopPropagation
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from ..core.database import db
from ..config import config
from ..helpers.premium import render


def register(app, call):

    async def gate(client, message):
        if not message.from_user:
            return

        user_id = message.from_user.id

        if user_id == config.OWNER_ID:
            return

        # Global Ban
        if await db.is_gbanned(user_id):
            doc = await db.get_gban(user_id)
            reason = (
                doc.get("reason", "No reason provided")
                if doc
                else "No reason provided"
            )

            await message.reply_text(
                render(
                    f""":error: <b>Access Restricted</b>

<blockquote>
:warning: Your account has been globally restricted from using this bot.

:receipt: <b>Reason:</b>
<code>{reason}</code>

:support: If you believe this was issued by mistake, please contact the bot owner.
</blockquote>"""
                ),
                parse_mode=ParseMode.HTML,
            )
            raise StopPropagation

        # Maintenance Mode
        if await db.is_maintenance():
            if message.text and message.text.startswith("/"):
                await message.reply_text(
                    render(
                        """:settings: <b>Scheduled Maintenance</b>

<blockquote>
:rocket: We're currently polishing new features and improving your music experience.

:tools: The bot is temporarily unavailable while maintenance is in progress.

:heart: Thank you for your patience and support.
We'll be back online very soon with an even better experience.
</blockquote>"""
                    ),
                    parse_mode=ParseMode.HTML,
                )
                raise StopPropagation

    app.add_handler(
        MessageHandler(
            gate,
            filters.all,
        ),
        group=-1,
    )