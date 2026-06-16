# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions

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

        is_admin = False
        is_auth = False

        try:
            member = await client.get_chat_member(
                message.chat.id,
                message.from_user.id,
            )
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


def register(app, call):

    async def auth(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await message.reply_text(
                    "<blockquote><b>🛡 Auth — Usage</b></blockquote>\n\n"
                    "❖ Reply to a user's message with <b>/auth</b>\n"
                    "┗ Grants them permission to control music playback.",
                    link_preview_options=_LP,
                )

            user = target.from_user
            chat_id = message.chat.id

            if await db.is_auth(chat_id, user.id):
                return await message.reply_text(
                    f"<blockquote><b>🛡 Already Authorised</b></blockquote>\n\n"
                    f"❖ {user.mention} already has playback permissions.",
                    link_preview_options=_LP,
                )

            await db.auth_user(chat_id, user.id)
            await action_log("🛡 Auth User", message)

            await message.reply_text(
                f"<blockquote><b>✅ User Authorised</b></blockquote>\n\n"
                f"❖ <b>User :</b> {user.mention}\n"
                f"❖ <b>Permission :</b> Music playback control\n\n"
                f"<blockquote>They can now control music playback.</blockquote>",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Auth Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Auth Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def unauth(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await message.reply_text(
                    "<blockquote><b>🛡 Unauth — Usage</b></blockquote>\n\n"
                    "❖ Reply to a user's message with <b>/unauth</b>\n"
                    "┗ Revokes their playback permissions.",
                    link_preview_options=_LP,
                )

            user = target.from_user
            chat_id = message.chat.id

            if not await db.is_auth(chat_id, user.id):
                return await message.reply_text(
                    f"<blockquote><b>🛡 Not Authorised</b></blockquote>\n\n"
                    f"❖ {user.mention} has no special permissions here.",
                    link_preview_options=_LP,
                )

            await db.unauth_user(chat_id, user.id)
            await action_log("🛡 Unauth User", message)

            await message.reply_text(
                f"<blockquote><b>🚫 Access Revoked</b></blockquote>\n\n"
                f"❖ <b>User :</b> {user.mention}\n"
                f"❖ <b>Status :</b> Playback permissions removed.",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Unauth Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Unauth Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def authlist(client, message):
        try:
            users = await db.get_auth_users(message.chat.id)

            if not users:
                return await message.reply_text(
                    "<blockquote><b>🛡 Authorised Users</b></blockquote>\n\n"
                    "No users have been authorised in this group yet.",
                    link_preview_options=_LP,
                )

            lines = []

            for i, uid in enumerate(users, start=1):
                try:
                    u = await client.get_users(uid)
                    name = u.mention
                except Exception:
                    name = f"<code>{uid}</code>"

                lines.append(f"❖ <b>{i}.</b> {name}")

            await message.reply_text(
                "<blockquote><b>🛡 Authorised Users</b></blockquote>\n\n"
                + "\n".join(lines)
                + f"\n\n<blockquote>♫ Total authorised users: {len(users)}</blockquote>",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Authlist Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Authlist Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def blacklistchat(client, message):
        try:
            chat_id = message.chat.id

            if await db.is_blacklisted(chat_id):
                return await message.reply_text(
                    "<blockquote><b>🚫 Already Blacklisted</b></blockquote>\n\n"
                    "This group is already blacklisted.",
                    link_preview_options=_LP,
                )

            await db.blacklist_chat(chat_id)
            await action_log("🚫 Blacklist Chat", message)

            await message.reply_text(
                "<blockquote><b>🚫 Group Blacklisted</b></blockquote>\n\n"
                "❖ <b>Status :</b> Bot disabled in this group.",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Blacklistchat Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Blacklist Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def whitelistchat(client, message):
        try:
            chat_id = message.chat.id

            if not await db.is_blacklisted(chat_id):
                return await message.reply_text(
                    "<blockquote><b>✅ Already Active</b></blockquote>\n\n"
                    "This group is not blacklisted.",
                    link_preview_options=_LP,
                )

            await db.whitelist_chat(chat_id)
            await action_log("✅ Whitelist Chat", message)

            await message.reply_text(
                "<blockquote><b>✅ Group Whitelisted</b></blockquote>\n\n"
                "❖ <b>Status :</b> Bot re-enabled successfully.",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Whitelistchat Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Whitelist Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def pause(client, message):
        try:
            chat_id = message.chat.id

            if chat_id not in active:
                return await message.reply_text(
                    "<blockquote><b>⏸ Pause</b></blockquote>\n\n"
                    "There is no active stream to pause.",
                    link_preview_options=_LP,
                )

            await call.pause(chat_id)
            await action_log("⏸ Pause", message)

            await message.reply_text(
                "<blockquote><b>⏸ Playback Paused</b></blockquote>\n\n"
                f"❖ <b>Track :</b> {get_track_title(chat_id)}\n\n"
                "<blockquote>♫ Use /resume to continue.</blockquote>",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Pause Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Pause Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def resume(client, message):
        try:
            chat_id = message.chat.id

            if chat_id not in active:
                return await message.reply_text(
                    "<blockquote><b>▶️ Resume</b></blockquote>\n\n"
                    "There is no active stream in this chat.",
                    link_preview_options=_LP,
                )

            await call.resume(chat_id)
            await action_log("▶️ Resume", message)

            await message.reply_text(
                "<blockquote><b>▶️ Playback Resumed</b></blockquote>\n\n"
                f"❖ <b>Track :</b> {get_track_title(chat_id)}\n\n"
                "<blockquote>♫ Enjoy the music!</blockquote>",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Resume Command", e)
            await message.reply_text(
                f"<blockquote><b>❌ Resume Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    app.add_handler(MessageHandler(auth, filters.command("auth") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(unauth, filters.command("unauth") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(authlist, filters.command("authlist") & group_filter))
    app.add_handler(MessageHandler(blacklistchat, filters.command("blacklistchat") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(whitelistchat, filters.command("whitelistchat") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(pause, filters.command("pause") & group_filter & admin_or_auth))
    app.add_handler(MessageHandler(resume, filters.command("resume") & group_filter & admin_or_auth))