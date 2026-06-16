# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import traceback
from datetime import datetime

from pyrogram.types import LinkPreviewOptions

from jass import app, logger
from jass.config import config

_LP = LinkPreviewOptions(is_disabled=True)

IMPORTANT_ACTIONS = {
    "📢 Broadcast Started",
    "📢 Broadcast Completed",
    "➕ Bot Added To Group",
    "📝 Logger Enabled",
    "📝 Logger Disabled",
}


def now():
    return datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")


async def _is_logging_enabled() -> bool:
    try:
        from jass.core.database import db

        await db.connect()
        doc = await db.db.config.find_one({"_id": "logger"})
        return doc.get("enabled", True) if doc else True
    except Exception:
        return True


async def send_log(text: str, force: bool = False):
    chat_id = getattr(config, "LOGGER_CHAT_ID", 0)

    if not chat_id:
        logger.warning("LOGGER_CHAT_ID not set — skipping log")
        return

    if not force and not await _is_logging_enabled():
        return

    try:
        await app.send_message(
            chat_id,
            text,
            link_preview_options=_LP,
        )
    except Exception as e:
        logger.error(f"Logger group failed: {e}")


async def startup_log():
    await send_log(
        f"""<blockquote><b>✅ Bot Started</b></blockquote>

❖ <b>Status :</b> Running
❖ <b>Time :</b> <code>{now()}</code>""",
        force=True,
    )


async def start_command_log(message):
    user = message.from_user
    chat = message.chat

    await send_log(
        f"""<blockquote><b>🚀 Start Command</b></blockquote>

❖ <b>User :</b> {user.mention if user else 'Unknown'}
❖ <b>User ID :</b> <code>{user.id if user else 'None'}</code>
❖ <b>Username :</b> @{user.username if user and user.username else 'None'}

❖ <b>Chat :</b> {chat.title or 'Private'}
❖ <b>Chat ID :</b> <code>{chat.id}</code>
❖ <b>Time :</b> <code>{now()}</code>"""
    )


async def play_command_log(message, query: str):
    user = message.from_user
    chat = message.chat

    await send_log(
        f"""<blockquote><b>🎵 Play Request</b></blockquote>

❖ <b>Query :</b> <code>{query}</code>

❖ <b>User :</b> {user.mention if user else 'Unknown'}
❖ <b>User ID :</b> <code>{user.id if user else 'None'}</code>

❖ <b>Chat :</b> {chat.title or 'Private'}
❖ <b>Chat ID :</b> <code>{chat.id}</code>
❖ <b>Time :</b> <code>{now()}</code>"""
    )


async def action_log(title: str, message):
    if title not in IMPORTANT_ACTIONS:
        return

    user = message.from_user
    chat = message.chat

    await send_log(
        f"""<blockquote><b>{title}</b></blockquote>

❖ <b>User :</b> {user.mention if user else 'Unknown'}
❖ <b>Chat :</b> {chat.title or 'Private'}
❖ <b>Chat ID :</b> <code>{chat.id}</code>
❖ <b>Time :</b> <code>{now()}</code>"""
    )


async def error_log(where: str, error: Exception):
    chat_id = getattr(config, "LOGGER_CHAT_ID", 0)

    if not chat_id:
        logger.error(f"[{where}] {error}")
        return

    try:
        await app.send_message(
            chat_id,
            f"""<blockquote><b>⚠️ Error — {where}</b></blockquote>

❖ <b>Error :</b> <code>{error}</code>

<pre>{traceback.format_exc()[-2500:]}</pre>""",
            link_preview_options=_LP,
        )
    except Exception as e:
        logger.error(f"Logger group failed: {e}")