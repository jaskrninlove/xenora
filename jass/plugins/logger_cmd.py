# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

"""
plugins/logger_cmd.py
─────────────────────
/logger on|off — owner-only toggle for live logging to LOGGER_CHAT_ID.
"""
from pyrogram.enums import ParseMode
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions

from ..config import config
from ..core.database import db
from ..core.logger import action_log, error_log
from ..helpers.premium import render

_LP = LinkPreviewOptions(is_disabled=True)


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


def register(app, call):

    async def logger_cmd(client, message):
        try:
            if not (message.from_user and message.from_user.id == config.OWNER_ID):
                return await premium_reply(
                    message,
                    ":error: <b>Access Denied</b>\n\n"
                    "<blockquote>This command is reserved exclusively for the bot owner.</blockquote>",
                )

            args = message.command[1].lower() if len(message.command) > 1 else None

            if args not in ("on", "off"):
                try:
                    doc = await db.db.config.find_one({"_id": "logger"})
                    current = doc.get("enabled", True) if doc else True
                except Exception:
                    current = True

                chat_id = getattr(config, "LOGGER_CHAT_ID", "Not set")

                return await premium_reply(
                    message,
                    ":receipt: <b>Logger Usage</b>\n\n"
                    "<blockquote>"
                    ":success: <b>/logger on</b> — Enable live logging to log channel\n"
                    ":error: <b>/logger off</b> — Disable channel logging\n\n"
                    f":signal: <b>Current Status:</b> <code>{'ON' if current else 'OFF'}</code>\n"
                    f":chat: <b>Log Channel:</b> <code>{chat_id}</code>\n\n"
                    "Only the bot owner can toggle this."
                    "</blockquote>",
                )

            state = args == "on"

            await db.connect()
            await db.db.config.update_one(
                {"_id": "logger"},
                {"$set": {"enabled": state}},
                upsert=True,
            )

            await action_log(f"Logger {'Enabled' if state else 'Disabled'}", message)

            await premium_reply(
                message,
                f":receipt: <b>Logger {'Enabled' if state else 'Disabled'}</b>\n\n"
                f"<blockquote>"
                f":signal: <b>Status:</b> <code>{'ON' if state else 'OFF'}</code>\n"
                + (
                    ":success: <b>Effect:</b> All commands and actions will be logged to the channel.\n\n"
                    "Run /logger off to stop logging."
                    if state
                    else
                    ":warning: <b>Effect:</b> No logs will be sent to the channel until re-enabled.\n\n"
                    "Run /logger on to resume logging."
                )
                + "</blockquote>",
            )

        except Exception as e:
            await error_log("Logger Command", e)
            await premium_reply(
                message,
                f":error: <b>Logger Toggle Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(logger_cmd, filters.command("logger")))