# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import random

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import LinkPreviewOptions

from ..core.queue import queue
from ..core.player import active, loop_enabled
from ..core.logger import action_log, error_log

_LP = LinkPreviewOptions(is_disabled=True)


def get_title(track):
    return getattr(track, "title", "Unknown Track")


def register(app, call):

    async def shuffle(client, message):
        try:
            chat_id = message.chat.id
            items = queue.list(chat_id)

            if not items:
                return await message.reply_text(
                    "<blockquote><b>🔀 Shuffle</b></blockquote>\n\n"
                    "The queue is empty — nothing to shuffle.\n\n"
                    "<blockquote>♫ Use /play to add tracks first.</blockquote>",
                    link_preview_options=_LP,
                )

            shuffled = list(items)
            random.shuffle(shuffled)
            queue._queue[chat_id] = shuffled

            await action_log("🔀 Shuffle", message)
            await message.reply_text(
                f"""<blockquote><b>🔀 Queue Shuffled</b></blockquote>

❖ <b>Tracks Shuffled :</b> <code>{len(shuffled)}</code>

<blockquote>♫ The queue order has been randomised.</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Shuffle", e)
            await message.reply_text(
                f"<blockquote><b>❌ Shuffle Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def loop(client, message):
        try:
            chat_id = message.chat.id
            arg = message.command[1].lower() if len(message.command) > 1 else None
            current = loop_enabled.get(chat_id, False)

            if arg not in ("on", "off"):
                return await message.reply_text(
                    f"""<blockquote><b>🔁 Loop — Usage</b></blockquote>

❖ <b>/loop on</b> — Repeat the current track
❖ <b>/loop off</b> — Continue queue normally

❖ <b>Current Status :</b> <code>{"ON" if current else "OFF"}</code>""",
                    link_preview_options=_LP,
                )

            if chat_id not in active:
                return await message.reply_text(
                    "<blockquote><b>🔁 Loop</b></blockquote>\n\n"
                    "There is no active stream in this chat.\n\n"
                    "<blockquote>♫ Start one with /play first.</blockquote>",
                    link_preview_options=_LP,
                )

            state = arg == "on"
            loop_enabled[chat_id] = state
            track = active.get(chat_id)

            await action_log(f"🔁 Loop {'On' if state else 'Off'}", message)
            await message.reply_text(
                f"""<blockquote><b>🔁 Loop {"Enabled" if state else "Disabled"}</b></blockquote>

❖ <b>Track :</b> {get_title(track)}
❖ <b>Status :</b> <code>{"ON — current track will repeat" if state else "OFF — queue will advance normally"}</code>

<blockquote>♫ {"Use /loop off to return to normal playback." if state else "The queue will now continue normally."}</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Loop", e)
            await message.reply_text(
                f"<blockquote><b>❌ Loop Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def volume(client, message):
        try:
            chat_id = message.chat.id

            if len(message.command) < 2 or not message.command[1].isdigit():
                return await message.reply_text(
                    "<blockquote><b>🔊 Volume — Usage</b></blockquote>\n\n"
                    "❖ <b>/volume</b> <code>[1–200]</code>",
                    link_preview_options=_LP,
                )

            vol = int(message.command[1])

            if not 1 <= vol <= 200:
                return await message.reply_text(
                    "<blockquote><b>🔊 Invalid Volume</b></blockquote>\n\n"
                    "Volume must be between <code>1</code> and <code>200</code>.",
                    link_preview_options=_LP,
                )

            if chat_id not in active:
                return await message.reply_text(
                    "<blockquote><b>🔊 Volume</b></blockquote>\n\n"
                    "There is no active stream in this chat.",
                    link_preview_options=_LP,
                )

            await call.change_volume_call(chat_id, vol)
            await action_log(f"🔊 Volume → {vol}", message)

            filled = int(vol / 200 * 10)
            bar = "█" * filled + "░" * (10 - filled)

            await message.reply_text(
                f"""<blockquote><b>🔊 Volume Updated</b></blockquote>

❖ <b>Level :</b> [{bar}] <code>{vol}%</code>

<blockquote>♫ Playback volume updated.</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Volume", e)
            await message.reply_text(
                f"<blockquote><b>❌ Volume Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def seek(client, message):
        await message.reply_text(
            """<blockquote><b>⚠️ Seek Unavailable</b></blockquote>

This PyTgCalls version does not support stream seeking.

<blockquote>♫ Use /skip or /play again to control playback.</blockquote>""",
            link_preview_options=_LP,
        )

    async def clearqueue(client, message):
        try:
            chat_id = message.chat.id
            items = queue.list(chat_id)

            if not items:
                return await message.reply_text(
                    "<blockquote><b>🗑 Clear Queue</b></blockquote>\n\n"
                    "The queue is already empty.\n\n <blockquote>♫ Use /play to add tracks.</blockquote>",
                    link_preview_options=_LP,
                )

            count = len(items)
            queue.clear(chat_id)

            await action_log("🗑 Clear Queue", message)
            await message.reply_text(
                f"""<blockquote><b>🗑 Queue Cleared</b></blockquote>

❖ <b>Tracks Removed :</b> <code>{count}</code>

<blockquote>♫ Current track will continue playing.</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("ClearQueue", e)
            await message.reply_text(
                f"<blockquote><b>❌ Clear Queue Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    async def remove(client, message):
        try:
            chat_id = message.chat.id

            if len(message.command) < 2 or not message.command[1].isdigit():
                return await message.reply_text(
                    "<blockquote><b>🗑 Remove — Usage</b></blockquote>\n\n"
                    "❖ <b>/remove</b> <code>[position]</code>\n\n <blockquote>♫ Use /queue to see position numbers.</blockquote>",
                    link_preview_options=_LP,
                )

            pos = int(message.command[1])
            items = queue.list(chat_id)

            if not items:
                return await message.reply_text(
                    "<blockquote><b>🗑 Remove</b></blockquote>\n\n"
                    "The queue is empty.",
                    link_preview_options=_LP,
                )

            if not 1 <= pos <= len(items):
                return await message.reply_text(
                    f"<blockquote><b>🗑 Invalid Position</b></blockquote>\n\n"
                    f"Queue has <code>{len(items)}</code> track(s).",
                    link_preview_options=_LP,
                )

            removed = items.pop(pos - 1)
            queue._queue[chat_id] = items

            await action_log(f"🗑 Remove #{pos}", message)
            await message.reply_text(
                f"""<blockquote><b>🗑 Track Removed</b></blockquote>

❖ <b>Position :</b> <code>#{pos}</code>
❖ <b>Title :</b> {get_title(removed)}

<blockquote>♫ {len(items)} track(s) remaining.</blockquote>""",
                link_preview_options=_LP,
            )

        except Exception as e:
            await error_log("Remove", e)
            await message.reply_text(
                f"<blockquote><b>❌ Remove Failed</b></blockquote>\n\n"
                f"❖ <b>Error :</b> <code>{e}</code>",
                link_preview_options=_LP,
            )

    app.add_handler(MessageHandler(shuffle, filters.command("shuffle")))
    app.add_handler(MessageHandler(loop, filters.command("loop")))
    app.add_handler(MessageHandler(volume, filters.command("volume")))
    app.add_handler(MessageHandler(seek, filters.command("seek")))
    app.add_handler(MessageHandler(clearqueue, filters.command(["clearqueue", "cq"])))
    app.add_handler(MessageHandler(remove, filters.command(["remove", "rm"])))