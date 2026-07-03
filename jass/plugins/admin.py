# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification,
# distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions
from pyrogram.enums import ParseMode
from ..helpers.premium import render
from ..core.player import active
from ..core.logger import action_log, error_log
from ..core.database import db

_LP = LinkPreviewOptions(is_disabled=True)


def _is_group():
    async def func(_, client, message):
        return message.chat.type.name in ["GROUP", "SUPERGROUP"]
    return filters.create(func)


def _is_admin_or_auth():
    async def func(_, client, message):
        if not message.from_user:
            return False

        if message.chat.type.name not in ["GROUP", "SUPERGROUP"]:
            return False

        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = member.status.name in ["OWNER", "ADMINISTRATOR"]
        except Exception:
            is_admin = False

        try:
            is_auth = await db.is_auth(message.chat.id, message.from_user.id)
        except Exception:
            is_auth = False

        return is_admin or is_auth

    return filters.create(func)


group_filter = _is_group()
admin_or_auth = _is_admin_or_auth()


def get_track_title(chat_id: int):
    return getattr(active.get(chat_id), "title", "Unknown Track")


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


def register(app, call):

    async def auth(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await premium_reply(
                    message,
                    ":settings: <b>Auth Usage</b>\n\n"
                    "<blockquote>"
                    ":profile: Reply to a user's message with <b>/auth</b>\n"
                    ":success: Grants them permission to control music playback."
                    "</blockquote>",
                )

            user = target.from_user
            chat_id = message.chat.id

            if await db.is_auth(chat_id, user.id):
                return await premium_reply(
                    message,
                    f":warning: <b>Already Authorised</b>\n\n"
                    f"<blockquote>{user.mention} already has playback permissions.</blockquote>",
                )

            await db.auth_user(chat_id, user.id)
            await action_log("Auth User", message)

            await premium_reply(
                message,
                f":success: <b>User Authorised</b>\n\n"
                f"<blockquote>"
                f":profile: <b>User:</b> {user.mention}\n"
                f":settings: <b>Permission:</b> Music playback control\n\n"
                f"They can now control music playback."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Auth Command", e)
            await premium_reply(
                message,
                f":error: <b>Auth Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def unauth(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await premium_reply(
                    message,
                    ":settings: <b>Unauth Usage</b>\n\n"
                    "<blockquote>"
                    ":profile: Reply to a user's message with <b>/unauth</b>\n"
                    ":warning: Revokes their playback permissions."
                    "</blockquote>",
                )

            user = target.from_user
            chat_id = message.chat.id

            if not await db.is_auth(chat_id, user.id):
                return await premium_reply(
                    message,
                    f":warning: <b>Not Authorised</b>\n\n"
                    f"<blockquote>{user.mention} has no special permissions here.</blockquote>",
                )

            await db.unauth_user(chat_id, user.id)
            await action_log("Unauth User", message)

            await premium_reply(
                message,
                f":error: <b>Access Revoked</b>\n\n"
                f"<blockquote>"
                f":profile: <b>User:</b> {user.mention}\n"
                f":settings: <b>Status:</b> Playback permissions removed."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Unauth Command", e)
            await premium_reply(
                message,
                f":error: <b>Unauth Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def authlist(client, message):
        try:
            users = await db.get_auth_users(message.chat.id)

            if not users:
                return await premium_reply(
                    message,
                    ":settings: <b>Authorised Users</b>\n\n"
                    "<blockquote>No users have been authorised in this group yet.</blockquote>",
                )

            lines = []

            for i, uid in enumerate(users, start=1):
                try:
                    u = await client.get_users(uid)
                    name = u.mention
                except Exception:
                    name = f"<code>{uid}</code>"

                lines.append(f":profile: <b>{i}.</b> {name}")

            await premium_reply(
                message,
                ":settings: <b>Authorised Users</b>\n\n"
                + "\n".join(lines)
                + f"\n\n<blockquote>:success: Total authorised users: <code>{len(users)}</code></blockquote>",
            )

        except Exception as e:
            await error_log("Authlist Command", e)
            await premium_reply(
                message,
                f":error: <b>Authlist Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def blacklistchat(client, message):
        try:
            chat_id = message.chat.id

            if await db.is_blacklisted(chat_id):
                return await premium_reply(
                    message,
                    ":error: <b>Already Blacklisted</b>\n\n"
                    "<blockquote>This group is already blacklisted.</blockquote>",
                )

            await db.blacklist_chat(chat_id)
            await action_log("Blacklist Chat", message)

            await premium_reply(
                message,
                ":error: <b>Group Blacklisted</b>\n\n"
                "<blockquote>:settings: <b>Status:</b> Bot disabled in this group.</blockquote>",
            )

        except Exception as e:
            await error_log("Blacklistchat Command", e)
            await premium_reply(
                message,
                f":error: <b>Blacklist Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def whitelistchat(client, message):
        try:
            chat_id = message.chat.id

            if not await db.is_blacklisted(chat_id):
                return await premium_reply(
                    message,
                    ":success: <b>Already Active</b>\n\n"
                    "<blockquote>This group is not blacklisted.</blockquote>",
                )

            await db.whitelist_chat(chat_id)
            await action_log("Whitelist Chat", message)

            await premium_reply(
                message,
                ":success: <b>Group Whitelisted</b>\n\n"
                "<blockquote>:settings: <b>Status:</b> Bot re-enabled successfully.</blockquote>",
            )

        except Exception as e:
            await error_log("Whitelistchat Command", e)
            await premium_reply(
                message,
                f":error: <b>Whitelist Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def pause(client, message):
        try:
            chat_id = message.chat.id

            if chat_id not in active:
                return await premium_reply(
                    message,
                    ":pause: <b>Pause</b>\n\n"
                    "<blockquote>There is no active stream to pause.</blockquote>",
                )

            await call.pause(chat_id)
            await action_log("Pause", message)

            await premium_reply(
                message,
                ":pause: <b>Playback Paused</b>\n\n"
                f"<blockquote>"
                f":music: <b>Track:</b> {get_track_title(chat_id)}\n\n"
                f"Use /resume to continue."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Pause Command", e)
            await premium_reply(
                message,
                f":error: <b>Pause Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def resume(client, message):
        try:
            chat_id = message.chat.id

            if chat_id not in active:
                return await premium_reply(
                    message,
                    ":play: <b>Resume</b>\n\n"
                    "<blockquote>There is no active stream in this chat.</blockquote>",
                )

            await call.resume(chat_id)
            await action_log("Resume", message)

            await premium_reply(
                message,
                ":play: <b>Playback Resumed</b>\n\n"
                f"<blockquote>"
                f":music: <b>Track:</b> {get_track_title(chat_id)}\n\n"
                f"Enjoy the music."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Resume Command", e)
            await premium_reply(
                message,
                f":error: <b>Resume Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(auth, filters.command("auth") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(unauth, filters.command("unauth") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(authlist, filters.command("authlist") & group_filter))
    app.add_handler(MessageHandler(blacklistchat, filters.command("blacklistchat") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(whitelistchat, filters.command("whitelistchat") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(pause, filters.command("pause") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(resume, filters.command("resume") & group_filter & admin_or_auth))