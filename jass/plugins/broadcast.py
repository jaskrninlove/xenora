# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import asyncio

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions
from pyrogram.errors import (
    FloodWait,
    UserIsBlocked,
    InputUserDeactivated,
    PeerIdInvalid,
    ChatWriteForbidden,
    UserNotParticipant,
)

from ..config import config
from ..core.database import db
from ..core.logger import action_log, error_log

_LP = LinkPreviewOptions(is_disabled=True)


def _owner_filter():
    async def func(_, client, message):
        return bool(message.from_user and message.from_user.id == config.OWNER_ID)

    return filters.create(func)


async def _send_to(chat_id: int, replied_message) -> str:
    try:
        await replied_message.copy(
            chat_id=chat_id,
            reply_markup=replied_message.reply_markup,
        )
        return "ok"

    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        return await _send_to(chat_id, replied_message)

    except (UserIsBlocked, InputUserDeactivated):
        return "blocked"

    except PeerIdInvalid:
        return "deleted"

    except (ChatWriteForbidden, UserNotParticipant):
        return "forbidden"

    except Exception:
        return "error"


async def _get_targets(mode: str):
    users = []
    groups = []

    if mode in ["users", "both"]:
        users = await db.get_all_users()

    if mode in ["groups", "both"]:
        try:
            groups = await db.get_all_chats()
        except AttributeError:
            groups = []

    return users, groups


def register(app, call):

    async def broadcast(client, message):
        try:
            if not message.reply_to_message:
                return await message.reply_text(
                    """<blockquote><b>📢 Broadcast — Usage</b></blockquote>

Reply to any message with:

❖ <code>/broadcast users</code>
❖ <code>/broadcast groups</code>
❖ <code>/broadcast both</code>

<b>Supported:</b>
Text, photos, videos, documents, stickers, audio, voice notes, captions and inline buttons.

<blockquote>The original formatting and buttons will be preserved.</blockquote>""",
                    link_preview_options=_LP,
                )

            mode = "both"

            if len(message.command) > 1:
                mode = message.command[1].lower()

            if mode not in ["users", "groups", "both"]:
                return await message.reply_text(
                    """<blockquote><b>📢 Invalid Broadcast Mode</b></blockquote>

Use one of these:

❖ <code>/broadcast users</code>
❖ <code>/broadcast groups</code>
❖ <code>/broadcast both</code>""",
                    link_preview_options=_LP,
                )

            replied = message.reply_to_message

            users, groups = await _get_targets(mode)
            targets = users + groups

            if not targets:
                return await message.reply_text(
                    f"""<blockquote><b>📭 No Recipients</b></blockquote>

No recipients found for mode: <code>{mode}</code>""",
                    link_preview_options=_LP,
                )

            await action_log(f"📢 Broadcast Started — {mode}", message)

            status_msg = await message.reply_text(
                f"""<blockquote><b>📢 Broadcast In Progress</b></blockquote>

❖ <b>Mode :</b> <code>{mode}</code>
❖ <b>Users :</b> <code>{len(users)}</code>
❖ <b>Groups :</b> <code>{len(groups)}</code>
❖ <b>Total Targets :</b> <code>{len(targets)}</code>

<blockquote>Sending message without changing formatting...</blockquote>""",
                link_preview_options=_LP,
            )

            stats = {
                "ok": 0,
                "blocked": 0,
                "deleted": 0,
                "forbidden": 0,
                "error": 0,
            }

            for index, chat_id in enumerate(targets, start=1):
                result = await _send_to(chat_id, replied)
                stats[result] += 1

                if index % 25 == 0 or index == len(targets):
                    try:
                        failed = (
                            stats["blocked"]
                            + stats["deleted"]
                            + stats["forbidden"]
                            + stats["error"]
                        )

                        await status_msg.edit_text(
                            f"""<blockquote><b>📢 Broadcast In Progress</b></blockquote>

❖ <b>Mode :</b> <code>{mode}</code>
❖ <b>Progress :</b> <code>{index} / {len(targets)}</code>
❖ <b>Delivered :</b> <code>{stats["ok"]}</code>
❖ <b>Failed :</b> <code>{failed}</code>

<blockquote>Please wait until delivery completes.</blockquote>""",
                            link_preview_options=_LP,
                        )
                    except Exception:
                        pass

                await asyncio.sleep(0.07)

            failed = (
                stats["blocked"]
                + stats["deleted"]
                + stats["forbidden"]
                + stats["error"]
            )

            await status_msg.edit_text(
                f"""<blockquote><b>📢 Broadcast Completed</b></blockquote>

<b>📊 Delivery Report</b>
❖ <b>Mode :</b> <code>{mode}</code>
❖ <b>Total Targets :</b> <code>{len(targets)}</code>
❖ <b>Users :</b> <code>{len(users)}</code>
❖ <b>Groups :</b> <code>{len(groups)}</code>

<b>✅ Result</b>
❖ <b>Delivered :</b> <code>{stats["ok"]}</code>
❖ <b>Failed :</b> <code>{failed}</code>

<b>🔍 Failure Breakdown</b>
❖ <b>Blocked Bot :</b> <code>{stats["blocked"]}</code>
❖ <b>Deleted Account :</b> <code>{stats["deleted"]}</code>
❖ <b>No Write Access :</b> <code>{stats["forbidden"]}</code>
❖ <b>Other Errors :</b> <code>{stats["error"]}</code>

<blockquote>♫ Broadcast finished successfully.</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Broadcast Command", e)
            await message.reply_text(
                f"""<blockquote><b>❌ Broadcast Failed</b></blockquote>

❖ <b>Error :</b> <code>{e}</code>""",
                link_preview_options=_LP,
            )

    app.add_handler(
        MessageHandler(
            broadcast,
            filters.command("broadcast") & _owner_filter(),
        )
    )