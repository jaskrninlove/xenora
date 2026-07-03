# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from ..core.player import active
from ..core.logger import action_log, error_log
from ..core.database import db
from ..config import config
from ..helpers.premium import render


def _owner_only():
    async def func(_, client, message):
        return message.from_user and message.from_user.id == config.OWNER_ID

    return filters.create(func)


owner_filter = _owner_only()


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
    )


def register(app, call):

    async def gban(client, message):
        try:
            target = message.reply_to_message
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"

            if not target or not target.from_user:
                return await premium_reply(
                    message,
                    ":error: <b>Global Ban Usage</b>\n\n"
                    "<blockquote>"
                    ":profile: Reply to a user's message with <b>/gban</b> <code>[reason]</code>\n"
                    ":warning: Globally bans the user from accessing the bot across all groups.\n\n"
                    "This action is restricted to the bot owner."
                    "</blockquote>",
                )

            user = target.from_user

            if user.id == config.OWNER_ID:
                return await premium_reply(
                    message,
                    ":warning: <b>Global Ban</b>\n\n"
                    "<blockquote>You cannot globally ban the bot owner.</blockquote>",
                )

            if await db.is_gbanned(user.id):
                return await premium_reply(
                    message,
                    f":warning: <b>Already Banned</b>\n\n"
                    f"<blockquote>{user.mention} is already globally banned.\n\n"
                    f"Use /ungban to lift the ban.</blockquote>",
                )

            await db.gban_user(user.id, reason)
            await action_log("Global Ban", message)

            await premium_reply(
                message,
                f":error: <b>Global Ban Issued</b>\n\n"
                f"<blockquote>"
                f":profile: <b>User:</b> {user.mention}\n"
                f":key: <b>ID:</b> <code>{user.id}</code>\n"
                f":receipt: <b>Reason:</b> {reason}\n\n"
                f"This user is now blocked from accessing the bot."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("GBan Command", e)
            await premium_reply(
                message,
                f":error: <b>GBan Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def ungban(client, message):
        try:
            target = message.reply_to_message

            if not target or not target.from_user:
                return await premium_reply(
                    message,
                    ":success: <b>Global Unban Usage</b>\n\n"
                    "<blockquote>"
                    ":profile: Reply to a user's message with <b>/ungban</b>\n"
                    ":success: Lifts a global ban and restores access to the bot.\n\n"
                    "This action is restricted to the bot owner."
                    "</blockquote>",
                )

            user = target.from_user

            if not await db.is_gbanned(user.id):
                return await premium_reply(
                    message,
                    f":warning: <b>Not Banned</b>\n\n"
                    f"<blockquote>{user.mention} is not globally banned.\n\n"
                    f"No action taken.</blockquote>",
                )

            await db.ungban_user(user.id)
            await action_log("Global Unban", message)

            await premium_reply(
                message,
                f":success: <b>Global Ban Lifted</b>\n\n"
                f"<blockquote>"
                f":profile: <b>User:</b> {user.mention}\n"
                f":key: <b>ID:</b> <code>{user.id}</code>\n"
                f":success: <b>Status:</b> Access restored\n\n"
                f"This user can now interact with the bot again."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("UnGBan Command", e)
            await premium_reply(
                message,
                f":error: <b>UnGBan Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def maintenance(client, message):
        try:
            args = message.command[1].lower() if len(message.command) > 1 else None

            if args not in ("on", "off"):
                current = await db.is_maintenance()
                return await premium_reply(
                    message,
                    ":settings: <b>Maintenance Usage</b>\n\n"
                    "<blockquote>"
                    ":success: <b>/maintenance on</b> — Enable maintenance mode\n"
                    ":error: <b>/maintenance off</b> — Disable maintenance mode\n\n"
                    f":signal: <b>Current Status:</b> <code>{'ON' if current else 'OFF'}</code>\n\n"
                    "While enabled, only the owner can use the bot."
                    "</blockquote>",
                )

            state = args == "on"
            await db.set_maintenance(state)
            await action_log(f"Maintenance {'ON' if state else 'OFF'}", message)

            await premium_reply(
                message,
                f":settings: <b>Maintenance Mode {'Enabled' if state else 'Disabled'}</b>\n\n"
                f"<blockquote>"
                f":signal: <b>Status:</b> <code>{'ON' if state else 'OFF'}</code>\n"
                + (
                    ":tools: <b>Effect:</b> Only the owner can use the bot right now.\n\n"
                    "Run /maintenance off when your work is complete."
                    if state
                    else
                    ":success: <b>Effect:</b> All users can access the bot normally.\n\n"
                    "The bot is back online for everyone."
                )
                + "</blockquote>",
            )

        except Exception as e:
            await error_log("Maintenance Command", e)
            await premium_reply(
                message,
                f":error: <b>Maintenance Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def activevc(client, message):
        try:
            await action_log("Active VC Command", message)

            if not active:
                return await premium_reply(
                    message,
                    ":active: <b>Active Voice Chats</b>\n\n"
                    "<blockquote>"
                    "There are no active streams at the moment.\n\n"
                    "Start one with /play or /vplay."
                    "</blockquote>",
                )

            lines = []
            for i, (chat_id, info) in enumerate(active.items(), start=1):
                title = info.get("title", "Unknown") if isinstance(info, dict) else "Unknown"
                mode = info.get("type", "audio") if isinstance(info, dict) else "audio"
                badge = ":video:" if mode == "video" else ":music:"
                lines.append(f"{badge} <b>{i}.</b> <code>{chat_id}</code> — {title}")

            await premium_reply(
                message,
                ":active: <b>Active Voice Chats</b>\n\n"
                "<blockquote>"
                + "\n".join(lines)
                + f"\n\n:success: <code>{len(active)}</code> stream(s) currently live."
                "</blockquote>",
            )

        except Exception as e:
            await error_log("ActiveVC Command", e)
            await premium_reply(
                message,
                f":error: <b>ActiveVC Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(gban, filters.command("gban") & owner_filter))
    app.add_handler(MessageHandler(ungban, filters.command("ungban") & owner_filter))
    app.add_handler(MessageHandler(maintenance, filters.command("maintenance") & owner_filter))
    app.add_handler(MessageHandler(activevc, filters.command(["activevc", "active"]) & owner_filter))