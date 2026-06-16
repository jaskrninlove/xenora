# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from ..core.player import active
from ..core.logger import action_log, error_log
from ..core.database import db
from ..config import config


def _owner_only():
    async def func(_, client, message):
        return message.from_user and message.from_user.id == config.OWNER_ID
    return filters.create(func)


owner_filter = _owner_only()


def register(app, call):

    # ── /gban ─────────────────────────────────────────────────────────────────
    async def gban(client, message):
        try:
            target = message.reply_to_message
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"

            if not target or not target.from_user:
                return await message.reply_text(
                    "<blockquote><b>🔨 Global Ban — Usage</b></blockquote>\n\n"
                    "❖ Reply to a user's message with <b>/gban</b> <code>[reason]</code>\n"
                    "┗ Globally bans the user from accessing the bot across all groups.\n\n"
                    "<blockquote>This action is restricted to the bot owner.</blockquote>"
                )

            user = target.from_user

            if user.id == config.OWNER_ID:
                return await message.reply_text(
                    "<blockquote><b>🔨 Global Ban</b></blockquote>\n\n"
                    "❖ You cannot globally ban the bot owner.\n\n"
                    "<blockquote>Nice try though.</blockquote>"
                )

            if await db.is_gbanned(user.id):
                return await message.reply_text(
                    f"<blockquote><b>🔨 Already Banned</b></blockquote>\n\n"
                    f"❖ {user.mention} is already globally banned.\n\n"
                    f"<blockquote>Use /ungban to lift the ban.</blockquote>"
                )

            await db.gban_user(user.id, reason)
            await action_log("🔨 Global Ban", message)
            await message.reply_text(
                f"<blockquote><b>🔨 Global Ban Issued</b></blockquote>\n\n"
                f"❖ <b>User :</b> {user.mention}\n"
                f"❖ <b>ID :</b> <code>{user.id}</code>\n"
                f"❖ <b>Reason :</b> {reason}\n\n"
                f"<blockquote>This user is now blocked from accessing the bot.</blockquote>"
            )
        except Exception as e:
            await error_log("GBan Command", e)
            await message.reply_text(f"<blockquote><b>❌ GBan Failed</b></blockquote>\n\n❖ <b>Error :</b> <code>{e}</code>")

    # ── /ungban ───────────────────────────────────────────────────────────────
    async def ungban(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await message.reply_text(
                    "<blockquote><b>🔓 Global Unban — Usage</b></blockquote>\n\n"
                    "❖ Reply to a user's message with <b>/ungban</b>\n"
                    "┗ Lifts a global ban, restoring the user's access to the bot.\n\n"
                    "<blockquote>This action is restricted to the bot owner.</blockquote>"
                )

            user = target.from_user

            if not await db.is_gbanned(user.id):
                return await message.reply_text(
                    f"<blockquote><b>🔓 Not Banned</b></blockquote>\n\n"
                    f"❖ {user.mention} is not globally banned.\n\n"
                    f"<blockquote>No action taken.</blockquote>"
                )

            await db.ungban_user(user.id)
            await action_log("🔓 Global Unban", message)
            await message.reply_text(
                f"<blockquote><b>✅ Global Ban Lifted</b></blockquote>\n\n"
                f"❖ <b>User :</b> {user.mention}\n"
                f"❖ <b>ID :</b> <code>{user.id}</code>\n"
                f"❖ <b>Status :</b> Access restored\n\n"
                f"<blockquote>This user can now interact with the bot again.</blockquote>"
            )
        except Exception as e:
            await error_log("UnGBan Command", e)
            await message.reply_text(f"<blockquote><b>❌ UnGBan Failed</b></blockquote>\n\n❖ <b>Error :</b> <code>{e}</code>")

    # ── /maintenance ──────────────────────────────────────────────────────────
    async def maintenance(client, message):
        try:
            args = message.command[1].lower() if len(message.command) > 1 else None

            if args not in ("on", "off"):
                current = await db.is_maintenance()
                return await message.reply_text(
                    "<blockquote><b>🔧 Maintenance — Usage</b></blockquote>\n\n"
                    "❖ <b>/maintenance on</b> — Enable maintenance mode\n"
                    "❖ <b>/maintenance off</b> — Disable maintenance mode\n\n"
                    f"❖ <b>Current Status :</b> <code>{'ON' if current else 'OFF'}</code>\n\n"
                    "<blockquote>While ON, only the owner can use the bot.</blockquote>"
                )

            state = args == "on"
            await db.set_maintenance(state)
            await action_log(f"🔧 Maintenance {'ON' if state else 'OFF'}", message)
            await message.reply_text(
                f"<blockquote><b>🔧 Maintenance Mode {'Enabled' if state else 'Disabled'}</b></blockquote>\n\n"
                f"❖ <b>Status :</b> <code>{'ON' if state else 'OFF'}</code>\n"
                + (
                    "❖ <b>Effect :</b> Only the owner can use the bot right now.\n\n"
                    "<blockquote>Run /maintenance off when work is complete.</blockquote>"
                    if state else
                    "❖ <b>Effect :</b> All users can access the bot normally.\n\n"
                    "<blockquote>♫ The bot is back online for everyone.</blockquote>"
                )
            )
        except Exception as e:
            await error_log("Maintenance Command", e)
            await message.reply_text(f"<blockquote><b>❌ Maintenance Failed</b></blockquote>\n\n❖ <b>Error :</b> <code>{e}</code>")

    # ── /activevc ─────────────────────────────────────────────────────────────
    async def activevc(client, message):
        try:
            await action_log("🎧 Active VC Command", message)

            if not active:
                return await message.reply_text(
                    "<blockquote><b>🎧 Active Voice Chats</b></blockquote>\n\n"
                    "There are no active streams at the moment.\n\n"
                    "<blockquote>♫ Start one with /play or /vplay.</blockquote>"
                )

            lines = []
            for i, (chat_id, info) in enumerate(active.items(), start=1):
                title = info.get("title", "Unknown") if isinstance(info, dict) else "Unknown"
                mode  = info.get("type", "audio")   if isinstance(info, dict) else "audio"
                badge = "🎬" if mode == "video" else "🎵"
                lines.append(f"{i}. {badge} <code>{chat_id}</code> — {title}")

            await message.reply_text(
                "<blockquote><b>🎧 Active Voice Chats</b></blockquote>\n\n"
                + "\n".join(lines)
                + f"\n\n<blockquote>♫ {len(active)} stream(s) currently live.</blockquote>"
            )
        except Exception as e:
            await error_log("ActiveVC Command", e)
            await message.reply_text(f"<blockquote><b>❌ ActiveVC Failed</b></blockquote>\n\n❖ <b>Error :</b> <code>{e}</code>")

    app.add_handler(MessageHandler(gban,        filters.command("gban")        & owner_filter))
    app.add_handler(MessageHandler(ungban,      filters.command("ungban")      & owner_filter))
    app.add_handler(MessageHandler(maintenance, filters.command("maintenance") & owner_filter))
    app.add_handler(MessageHandler(activevc,    filters.command(["activevc", "active"]) & owner_filter))