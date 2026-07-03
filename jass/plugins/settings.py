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
from pyrogram.enums import ParseMode
from ..core.database import db
from ..core.logger import action_log, error_log
from ..config import config
from ..helpers.premium import render

_LP = LinkPreviewOptions(is_disabled=True)

SUPPORTED_LANGS = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "ru": "Russian",
    "de": "German",
    "pt": "Portuguese",
    "tr": "Turkish",
    "id": "Indonesian",
}


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


async def _check_admin(message) -> bool:
    uid = message.from_user.id if message.from_user else None
    if not uid:
        return False

    if uid == config.OWNER_ID:
        return True

    if message.chat.type.value == "private":
        await premium_reply(
            message,
            ":error: <b>Access Denied</b>\n\n"
            "<blockquote>"
            ":settings: Settings can only be changed by group admins inside the group.\n\n"
            ":chat: Go to your group and run this command there."
            "</blockquote>",
        )
        return False

    try:
        member = await message.chat.get_member(uid)
        if member.status.value in ("administrator", "creator"):
            return True
    except Exception:
        pass

    await premium_reply(
        message,
        ":error: <b>Access Denied</b>\n\n"
        "<blockquote>"
        ":warning: Only group admins can change bot settings.\n\n"
        ":profile: Ask a group admin to run this command."
        "</blockquote>",
    )
    return False


def register(app, call):

    async def setplaymode(client, message):
        try:
            if not await _check_admin(message):
                return

            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in ("direct", "queue"):
                s = await db.get_settings(message.chat.id)
                current = s.get("playmode", "queue")

                return await premium_reply(
                    message,
                    ":settings: <b>Play Mode Usage</b>\n\n"
                    "<blockquote>"
                    ":play: <b>/setplaymode direct</b>\n"
                    "New songs play immediately and interrupt the current track.\n\n"
                    ":queue: <b>/setplaymode queue</b>\n"
                    "New songs are added to the end of the queue.\n\n"
                    f":signal: <b>Current Mode:</b> <code>{current.capitalize()}</code>\n\n"
                    "Only group admins can change this setting."
                    "</blockquote>",
                )

            await db.set_setting(message.chat.id, "playmode", args)
            await action_log(f"PlayMode -> {args}", message)

            await premium_reply(
                message,
                f":success: <b>Play Mode Updated</b>\n\n"
                f"<blockquote>"
                f":settings: <b>Mode:</b> <code>{args.capitalize()}</code>\n"
                + (
                    ":play: Songs will play immediately and interrupt the current track.\n\n"
                    if args == "direct"
                    else
                    ":queue: Songs will be added to the end of the queue.\n\n"
                )
                + "Applies to all future /play requests in this group."
                + "</blockquote>",
            )

        except Exception as e:
            await error_log("SetPlayMode", e)
            await premium_reply(
                message,
                f":error: <b>SetPlayMode Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def setstream(client, message):
        try:
            if not await _check_admin(message):
                return

            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in ("audio", "video"):
                s = await db.get_settings(message.chat.id)
                current = s.get("stream", "audio")

                return await premium_reply(
                    message,
                    ":signal: <b>Stream Type Usage</b>\n\n"
                    "<blockquote>"
                    ":music: <b>/setstream audio</b>\n"
                    "Stream audio only in the voice chat.\n\n"
                    ":video: <b>/setstream video</b>\n"
                    "Stream video in the voice chat.\n\n"
                    f":settings: <b>Current Type:</b> <code>{current.capitalize()}</code>\n\n"
                    "Only group admins can change this setting."
                    "</blockquote>",
                )

            await db.set_setting(message.chat.id, "stream", args)
            await action_log(f"Stream -> {args}", message)

            await premium_reply(
                message,
                f":success: <b>Stream Type Updated</b>\n\n"
                f"<blockquote>"
                f"{':music:' if args == 'audio' else ':video:'} "
                f"<b>Type:</b> <code>{args.capitalize()}</code>\n\n"
                f"Applies to all future streams in this group."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("SetStream", e)
            await premium_reply(
                message,
                f":error: <b>SetStream Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def setlang(client, message):
        try:
            if not await _check_admin(message):
                return

            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in SUPPORTED_LANGS:
                s = await db.get_settings(message.chat.id)
                current_code = s.get("lang", "en")
                current_name = SUPPORTED_LANGS.get(current_code, "English")
                lang_list = "\n".join(
                    f":language: <code>{code}</code> — {name}"
                    for code, name in SUPPORTED_LANGS.items()
                )

                return await premium_reply(
                    message,
                    ":language: <b>Language Usage</b>\n\n"
                    "<blockquote>"
                    ":settings: <b>/setlang</b> <code>[language code]</code>\n\n"
                    "<b>Supported Languages</b>\n"
                    f"{lang_list}\n\n"
                    f":signal: <b>Current Language:</b> {current_name}\n\n"
                    "Only group admins can change this setting."
                    "</blockquote>",
                )

            await db.set_setting(message.chat.id, "lang", args)
            await action_log(f"Lang -> {args}", message)

            await premium_reply(
                message,
                f":success: <b>Language Updated</b>\n\n"
                f"<blockquote>"
                f":language: <b>Language:</b> {SUPPORTED_LANGS[args]}\n"
                f":key: <b>Code:</b> <code>{args}</code>\n\n"
                f"Bot responses will now use {SUPPORTED_LANGS[args]} in this group."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("SetLang", e)
            await premium_reply(
                message,
                f":error: <b>SetLang Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def settings(client, message):
        try:
            s = await db.get_settings(message.chat.id)

            playmode = s.get("playmode", "queue").capitalize()
            stream = s.get("stream", "audio").capitalize()
            lang = SUPPORTED_LANGS.get(s.get("lang", "en"), "English")

            playmode_icon = ":queue:" if playmode.lower() == "queue" else ":play:"
            stream_icon = ":music:" if stream.lower() == "audio" else ":video:"

            await action_log("Settings", message)

            await premium_reply(
                message,
                ":settings: <b>Group Settings</b>\n\n"
                "<blockquote>"
                f"{playmode_icon} <b>Play Mode:</b> <code>{playmode}</code>\n"
                f"{stream_icon} <b>Stream Type:</b> <code>{stream}</code>\n"
                f":language: <b>Language:</b> {lang}\n\n"
                ":tools: <b>How To Change</b>\n"
                ":settings: /setplaymode <code>direct</code> or <code>queue</code>\n"
                ":signal: /setstream <code>audio</code> or <code>video</code>\n"
                ":language: /setlang <code>[language code]</code>\n\n"
                "Only group admins can modify these settings."
                "</blockquote>",
            )

        except Exception as e:
            await error_log("Settings", e)
            await premium_reply(
                message,
                f":error: <b>Settings Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(setplaymode, filters.command("setplaymode")))
    app.add_handler(MessageHandler(setstream, filters.command("setstream")))
    app.add_handler(MessageHandler(setlang, filters.command("setlang")))
    app.add_handler(MessageHandler(settings, filters.command("settings")))