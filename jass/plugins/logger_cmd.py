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
/logger on|off  — owner-only toggle for live logging to LOGGER_CHAT_ID.
Works by flipping a flag in the DB (config.LOGGER_CHAT_ID stays set,
but send_log() checks the flag and skips sending when disabled).
"""

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions

from ..config import config
from ..core.database import db
from ..core.logger import action_log, error_log

_LP = LinkPreviewOptions(is_disabled=True)


def register(app, call):

    async def logger_cmd(client, message):
        try:
            if not (message.from_user and message.from_user.id == config.OWNER_ID):
                return await message.reply_text(
                    "<blockquote><b>🚫 Access Denied</b></blockquote>\n\n"
                    "This command is reserved exclusively for the bot owner.",
                    link_preview_options=_LP,
                )

            args = message.command[1].lower() if len(message.command) > 1 else None

            if args not in ("on", "off"):
                # Show current state
                try:
                    doc     = await db.db.config.find_one({"_id": "logger"})
                    current = doc.get("enabled", True) if doc else True
                except Exception:
                    current = True

                chat_id = getattr(config, "LOGGER_CHAT_ID", "Not set")
                return await message.reply_text(
                    "<blockquote><b>📋 Logger — Usage</b></blockquote>\n\n"
                    "❖ <b>/logger on</b>  — Enable live logging to log channel\n"
                    "❖ <b>/logger off</b> — Disable logging (errors still print locally)\n\n"
                    f"❖ <b>Current Status :</b> <code>{'ON' if current else 'OFF'}</code>\n"
                    f"❖ <b>Log Channel :</b> <code>{chat_id}</code>\n\n"
                    "<blockquote>Only the bot owner can toggle this.</blockquote>",
                    link_preview_options=_LP,
                )

            state = args == "on"

            # Persist state in DB
            await db.connect()
            await db.db.config.update_one(
                {"_id": "logger"},
                {"$set": {"enabled": state}},
                upsert=True,
            )

            await action_log(f"📋 Logger {'Enabled' if state else 'Disabled'}", message)
            await message.reply_text(
                f"<blockquote><b>📋 Logger {'Enabled' if state else 'Disabled'}</b></blockquote>\n\n"
                f"❖ <b>Status :</b> <code>{'ON' if state else 'OFF'}</code>\n"
                + (
                    "❖ <b>Effect :</b> All commands and actions will be logged to the channel.\n\n"
                    "<blockquote>Run /logger off to stop logging.</blockquote>"
                    if state else
                    "❖ <b>Effect :</b> No logs will be sent to the channel until re-enabled.\n\n"
                    "<blockquote>Run /logger on to resume logging.</blockquote>"
                ),
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Logger Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Logger Toggle Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    app.add_handler(MessageHandler(logger_cmd, filters.command("logger")))