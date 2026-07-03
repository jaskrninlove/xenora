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
from pyrogram.enums import ParseMode

from ..config import config
from ..core.database import db
from ..core.logger import action_log, error_log
from ..helpers.premium import render

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


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


async def premium_edit(message, text: str):
    return await message.edit_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


def register(app, call):

    async def broadcast(client, message):
        try:
            if not message.reply_to_message:
                return await premium_reply(
                    message,
                    ":updates: <b>Broadcast Usage</b>\n\n"
                    "<blockquote>"
                    "Reply to any message with:\n\n"
                    ":profile: <code>/broadcast users</code>\n"
                    ":chat: <code>/broadcast groups</code>\n"
                    ":rocket: <code>/broadcast both</code>\n\n"
                    "<b>Supported:</b>\n"
                    "Text, photos, videos, documents, stickers, audio, voice notes, captions and inline buttons.\n\n"
                    "Original formatting and buttons will be preserved."
                    "</blockquote>",
                )

            mode = "both"

            if len(message.command) > 1:
                mode = message.command[1].lower()

            if mode not in ["users", "groups", "both"]:
                return await premium_reply(
                    message,
                    ":warning: <b>Invalid Broadcast Mode</b>\n\n"
                    "<blockquote>"
                    "Use one of these:\n\n"
                    ":profile: <code>/broadcast users</code>\n"
                    ":chat: <code>/broadcast groups</code>\n"
                    ":rocket: <code>/broadcast both</code>"
                    "</blockquote>",
                )

            replied = message.reply_to_message
            users, groups = await _get_targets(mode)
            targets = users + groups

            if not targets:
                return await premium_reply(
                    message,
                    f":mail: <b>No Recipients</b>\n\n"
                    f"<blockquote>No recipients found for mode: <code>{mode}</code></blockquote>",
                )

            await action_log(f"Broadcast Started — {mode}", message)

            status_msg = await premium_reply(
                message,
                f":updates: <b>Broadcast In Progress</b>\n\n"
                f"<blockquote>"
                f":settings: <b>Mode:</b> <code>{mode}</code>\n"
                f":profile: <b>Users:</b> <code>{len(users)}</code>\n"
                f":chat: <b>Groups:</b> <code>{len(groups)}</code>\n"
                f":target: <b>Total Targets:</b> <code>{len(targets)}</code>\n\n"
                f"Sending message without changing formatting."
                f"</blockquote>",
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

                        await premium_edit(
                            status_msg,
                            f":updates: <b>Broadcast In Progress</b>\n\n"
                            f"<blockquote>"
                            f":settings: <b>Mode:</b> <code>{mode}</code>\n"
                            f":chart: <b>Progress:</b> <code>{index} / {len(targets)}</code>\n"
                            f":success: <b>Delivered:</b> <code>{stats['ok']}</code>\n"
                            f":warning: <b>Failed:</b> <code>{failed}</code>\n\n"
                            f"Please wait until delivery completes."
                            f"</blockquote>",
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

            await premium_edit(
                status_msg,
                f":success: <b>Broadcast Completed</b>\n\n"
                f"<blockquote>"
                f":chart: <b>Delivery Report</b>\n\n"
                f":settings: <b>Mode:</b> <code>{mode}</code>\n"
                f":target: <b>Total Targets:</b> <code>{len(targets)}</code>\n"
                f":profile: <b>Users:</b> <code>{len(users)}</code>\n"
                f":chat: <b>Groups:</b> <code>{len(groups)}</code>\n\n"
                f":success: <b>Delivered:</b> <code>{stats['ok']}</code>\n"
                f":warning: <b>Failed:</b> <code>{failed}</code>\n\n"
                f":warning: <b>Failure Breakdown</b>\n"
                f":sad: <b>Blocked Bot:</b> <code>{stats['blocked']}</code>\n"
                f":error: <b>Deleted Account:</b> <code>{stats['deleted']}</code>\n"
                f":lock: <b>No Write Access:</b> <code>{stats['forbidden']}</code>\n"
                f":warning: <b>Other Errors:</b> <code>{stats['error']}</code>\n\n"
                f"Broadcast finished successfully."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Broadcast Command", e)
            await premium_reply(
                message,
                f":error: <b>Broadcast Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(
        MessageHandler(
            broadcast,
            filters.command("broadcast") & _owner_filter(),
        )
    )