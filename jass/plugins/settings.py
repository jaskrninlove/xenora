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

from ..core.database import db
from ..core.logger import action_log, error_log
from ..config import config

_LP = LinkPreviewOptions(is_disabled=True)

SUPPORTED_LANGS = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 Hindi",
    "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French",
    "ar": "🇸🇦 Arabic",
    "ru": "🇷🇺 Russian",
    "de": "🇩🇪 German",
    "pt": "🇧🇷 Portuguese",
    "tr": "🇹🇷 Turkish",
    "id": "🇮🇩 Indonesian",
}


async def _check_admin(message) -> bool:
    """
    Returns True if the user is allowed to change settings.
    - In private → owner only
    - In group   → group admin or bot owner
    Always sends a denial message itself and returns False if not allowed.
    """
    uid = message.from_user.id if message.from_user else None
    if not uid:
        return False

    # Owner always passes
    if uid == config.OWNER_ID:
        return True

    # Private chat — non-owners cannot change group settings here
    if message.chat.type.value == "private":
        await message.reply_text(
            "<blockquote><b>🚫 Access Denied</b></blockquote>\n\n"
            "Settings can only be changed by group admins inside the group.\n\n"
            "<blockquote>Go to your group and run this command there.</blockquote>",
            link_preview_options=_LP,
        )
        return False

    # Group — check admin status
    try:
        member = await message.chat.get_member(uid)
        if member.status.value in ("administrator", "creator"):
            return True
    except Exception:
        pass

    await message.reply_text(
        "<blockquote><b>🚫 Access Denied</b></blockquote>\n\n"
        "Only group admins can change bot settings.\n\n"
        "<blockquote>Ask a group admin to run this command.</blockquote>",
        link_preview_options=_LP,
    )
    return False


def register(app, call):

    # ── /setplaymode ──────────────────────────────────────────────────────────
    async def setplaymode(client, message):
        try:
            if not await _check_admin(message):
                return

            # Only take the first arg — ignore anything after a space
            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in ("direct", "queue"):
                s = await db.get_settings(message.chat.id)
                current = s.get("playmode", "queue")
                return await message.reply_text(
                    "<blockquote><b>🎛 Play Mode — Usage</b></blockquote>\n\n"
                    "❖ <b>/setplaymode direct</b>\n"
                    "┗ New songs play immediately, interrupting the current track.\n\n"
                    "❖ <b>/setplaymode queue</b>\n"
                    "┗ New songs are added to the end of the queue.\n\n"
                    f"❖ <b>Current Mode :</b> <code>{current.capitalize()}</code>\n\n"
                    "<blockquote>Only group admins can change this setting.</blockquote>",
                    link_preview_options=_LP,
                )

            await db.set_setting(message.chat.id, "playmode", args)
            await action_log(f"🎛 PlayMode → {args}", message)
            await message.reply_text(
                f"<blockquote><b>✅ Play Mode Updated</b></blockquote>\n\n"
                f"❖ <b>Mode :</b> <code>{args.capitalize()}</code>\n"
                + (
                    "┗ Songs will play immediately, interrupting the current track.\n\n"
                    if args == "direct" else
                    "┗ Songs will be added to the end of the queue.\n\n"
                )
                + "<blockquote>♫ Applies to all future /play requests in this group.</blockquote>",
                link_preview_options=_LP,
            )
        except Exception as e:
            await error_log("SetPlayMode", e)
            await message.reply_text(
                f"<blockquote><b>❌ SetPlayMode Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    # ── /setstream ────────────────────────────────────────────────────────────
    async def setstream(client, message):
        try:
            if not await _check_admin(message):
                return

            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in ("audio", "video"):
                s = await db.get_settings(message.chat.id)
                current = s.get("stream", "audio")
                return await message.reply_text(
                    "<blockquote><b>📡 Stream Type — Usage</b></blockquote>\n\n"
                    "❖ <b>/setstream audio</b>\n"
                    "┗ Stream audio only in the voice chat (default).\n\n"
                    "❖ <b>/setstream video</b>\n"
                    "┗ Stream video in the voice chat.\n\n"
                    f"❖ <b>Current Type :</b> <code>{current.capitalize()}</code>\n\n"
                    "<blockquote>Only group admins can change this setting.</blockquote>",
                    link_preview_options=_LP,
                )

            await db.set_setting(message.chat.id, "stream", args)
            await action_log(f"📡 Stream → {args}", message)
            badge = "🎵" if args == "audio" else "🎬"
            await message.reply_text(
                f"<blockquote><b>✅ Stream Type Updated</b></blockquote>\n\n"
                f"❖ <b>Type :</b> {badge} <code>{args.capitalize()}</code>\n\n"
                "<blockquote>♫ Applies to all future streams in this group.</blockquote>",
                link_preview_options=_LP,
            )
        except Exception as e:
            await error_log("SetStream", e)
            await message.reply_text(
                f"<blockquote><b>❌ SetStream Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    # ── /setlang ──────────────────────────────────────────────────────────────
    async def setlang(client, message):
        try:
            if not await _check_admin(message):
                return

            args = message.command[1].lower().strip() if len(message.command) > 1 else None

            if args not in SUPPORTED_LANGS:
                s            = await db.get_settings(message.chat.id)
                current_code = s.get("lang", "en")
                current_name = SUPPORTED_LANGS.get(current_code, "🇬🇧 English")
                lang_list    = "\n".join(
                    f"❖ <code>{code}</code> — {name}"
                    for code, name in SUPPORTED_LANGS.items()
                )
                return await message.reply_text(
                    "<blockquote><b>🌐 Language — Usage</b></blockquote>\n\n"
                    "❖ <b>/setlang</b> <code>[language code]</code>\n\n"
                    "<b>Supported Languages</b>\n"
                    + lang_list
                    + f"\n\n❖ <b>Current Language :</b> {current_name}\n\n"
                    "<blockquote>Only group admins can change this setting.</blockquote>",
                    link_preview_options=_LP,
                )

            await db.set_setting(message.chat.id, "lang", args)
            await action_log(f"🌐 Lang → {args}", message)
            await message.reply_text(
                f"<blockquote><b>✅ Language Updated</b></blockquote>\n\n"
                f"❖ <b>Language :</b> {SUPPORTED_LANGS[args]}\n"
                f"❖ <b>Code :</b> <code>{args}</code>\n\n"
                f"<blockquote>♫ Bot responses will now use {SUPPORTED_LANGS[args]} in this group.</blockquote>",
                link_preview_options=_LP,
            )
        except Exception as e:
            await error_log("SetLang", e)
            await message.reply_text(
                f"<blockquote><b>❌ SetLang Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    # ── /settings ─────────────────────────────────────────────────────────────
    async def settings(client, message):
        try:
            s = await db.get_settings(message.chat.id)

            playmode = s.get("playmode", "queue").capitalize()
            stream   = s.get("stream",   "audio").capitalize()
            lang     = SUPPORTED_LANGS.get(s.get("lang", "en"), "🇬🇧 English")

            stream_badge   = "🎵" if stream.lower()   == "audio" else "🎬"
            playmode_badge = "📋" if playmode.lower() == "queue" else "▶️"

            await action_log("🔧 Settings", message)
            await message.reply_text(
                "<blockquote><b>🔧 Group Settings</b></blockquote>\n\n"
                f"❖ {playmode_badge} <b>Play Mode :</b>   <code>{playmode}</code>\n"
                f"❖ {stream_badge} <b>Stream Type :</b> <code>{stream}</code>\n"
                f"❖ 🌐 <b>Language :</b>    {lang}\n\n"
                "<b>⚙ How to change</b>\n"
                "❖ /setplaymode <code>direct</code> or <code>queue</code>\n"
                "❖ /setstream <code>audio</code> or <code>video</code>\n"
                "❖ /setlang <code>[language code]</code>\n\n"
                "<blockquote>Only group admins can modify these settings.</blockquote>",
                link_preview_options=_LP,
            )
        except Exception as e:
            await error_log("Settings", e)
            await message.reply_text(
                f"<blockquote><b>❌ Settings Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    # No filter on handlers — permission is checked inside each function
    app.add_handler(MessageHandler(setplaymode, filters.command("setplaymode")))
    app.add_handler(MessageHandler(setstream,   filters.command("setstream")))
    app.add_handler(MessageHandler(setlang,     filters.command("setlang")))
    app.add_handler(MessageHandler(settings,    filters.command("settings")))