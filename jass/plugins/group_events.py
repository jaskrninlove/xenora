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
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    UserAlreadyParticipant,
    InviteHashExpired,
    InviteHashInvalid,
    ChatAdminRequired,
    UserNotParticipant,
    FloodWait,
    PeerIdInvalid,
)
from pyrogram.enums import ParseMode
from .. import assistant
from ..core.logger import action_log, error_log
from ..helpers.premium import render
from ..helpers.buttons import pbtn


UPDATES_URL = "https://t.me/Xenoraorg"


def _updates_button():
    return InlineKeyboardMarkup(
        [
            [
                pbtn(
                    "Updates",
                    url=UPDATES_URL,
                    icon_name="updates",
                    style="primary",
                )
            ]
        ]
    )


async def _premium_reply(message, text: str, **kwargs):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def _is_assistant_in_group(chat_id: int) -> bool:
    try:
        assistant_me = await assistant.get_me()
        member = await assistant.get_chat_member(chat_id, assistant_me.id)
        return member.status.value not in ("left", "banned", "kicked")
    except (UserNotParticipant, PeerIdInvalid):
        return False
    except Exception:
        return False


async def _try_join(invite_link: str) -> tuple[bool, str]:
    try:
        await assistant.join_chat(invite_link)
        return True, ""
    except UserAlreadyParticipant:
        return True, "already_in"
    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        return await _try_join(invite_link)
    except (InviteHashExpired, InviteHashInvalid):
        return False, "invite_invalid"
    except ChatAdminRequired:
        return False, "admin_required"
    except Exception as e:
        return False, str(e)


def _ready_text(bot_name: str, chat_title: str):
    return (
        f":bot: <b>{bot_name}</b>\n\n"
        f"<blockquote>"
        f":success: Thanks for adding me to <b>{chat_title}</b>.\n\n"
        f":active: <b>Assistant:</b> Connected automatically\n"
        f":music: <b>Music System:</b> Ready\n"
        f":play: <b>Voice Streaming:</b> Enabled\n\n"
        f"Start a voice chat and use /play to begin streaming."
        f"</blockquote>"
    )


def _needs_permission_text(bot_name: str, chat_title: str, reason: str):
    return (
        f":bot: <b>{bot_name}</b>\n\n"
        f"<blockquote>"
        f":warning: Thanks for adding me to <b>{chat_title}</b>.\n\n"
        f"I tried to connect my assistant automatically, but it could not join yet.\n\n"
        f":settings: <b>Required Permission:</b> Invite Users / Add Members\n"
        f":warning: <b>Reason:</b> <code>{reason}</code>\n\n"
        f"Give me invite permission, then send /start again in this group."
        f"</blockquote>"
    )


def register(app, call):

    async def on_bot_added(client, message):
        try:
            me = await client.get_me()

            if not message.new_chat_members:
                return

            added_ids = [user.id for user in message.new_chat_members]

            if me.id not in added_ids:
                return

            await action_log("Bot Added To Group", message)

            chat = message.chat
            chat_id = chat.id
            chat_title = chat.title or "this group"
            bot_name = me.first_name or "Music Bot"

            already_present = await _is_assistant_in_group(chat_id)

            if already_present:
                await _premium_reply(
                    message,
                    _ready_text(bot_name, chat_title),
                    reply_markup=_updates_button(),
                )
                return

            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except ChatAdminRequired:
                await _premium_reply(
                    message,
                    _needs_permission_text(
                        bot_name,
                        chat_title,
                        "Bot needs Invite Users permission.",
                    ),
                    reply_markup=_updates_button(),
                )
                return
            except Exception as e:
                await error_log("Export Invite Link", e)
                await _premium_reply(
                    message,
                    _needs_permission_text(
                        bot_name,
                        chat_title,
                        str(e),
                    ),
                    reply_markup=_updates_button(),
                )
                return

            success, reason = await _try_join(invite_link)

            if success:
                await _premium_reply(
                    message,
                    _ready_text(bot_name, chat_title),
                    reply_markup=_updates_button(),
                )
                return

            await _premium_reply(
                message,
                _needs_permission_text(
                    bot_name,
                    chat_title,
                    reason or "Assistant could not join automatically.",
                ),
                reply_markup=_updates_button(),
            )

        except Exception as e:
            await error_log("Bot Added Group Event", e)

    app.add_handler(
        MessageHandler(
            on_bot_added,
            filters.new_chat_members,
        )
    )