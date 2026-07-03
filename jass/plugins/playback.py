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
from pyrogram.enums import ParseMode
from ..core.queue import queue
from ..core.player import active, loop_enabled
from ..core.logger import action_log, error_log
from ..helpers.premium import render

_LP = LinkPreviewOptions(is_disabled=True)


def get_title(track):
    return getattr(track, "title", "Unknown Track")


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        link_preview_options=_LP,
    )


def register(app, call):

    async def shuffle(client, message):
        try:
            chat_id = message.chat.id
            items = queue.list(chat_id)

            if not items:
                return await premium_reply(
                    message,
                    ":shuffle: <b>Shuffle</b>\n\n"
                    "<blockquote>"
                    "The queue is empty. Nothing to shuffle.\n\n"
                    ":music: Use /play to add tracks first."
                    "</blockquote>",
                )

            shuffled = list(items)
            random.shuffle(shuffled)
            queue._queue[chat_id] = shuffled

            await action_log("Shuffle", message)
            await premium_reply(
                message,
                f":shuffle: <b>Queue Shuffled</b>\n\n"
                f"<blockquote>"
                f":queue: <b>Tracks Shuffled:</b> <code>{len(shuffled)}</code>\n\n"
                f"The queue order has been randomised."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Shuffle", e)
            await premium_reply(
                message,
                f":error: <b>Shuffle Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def loop(client, message):
        try:
            chat_id = message.chat.id
            arg = message.command[1].lower() if len(message.command) > 1 else None
            current = loop_enabled.get(chat_id, False)

            if arg not in ("on", "off"):
                return await premium_reply(
                    message,
                    f":loop: <b>Loop Usage</b>\n\n"
                    f"<blockquote>"
                    f":success: <b>/loop on</b> — Repeat the current track\n"
                    f":error: <b>/loop off</b> — Continue queue normally\n\n"
                    f":signal: <b>Current Status:</b> <code>{'ON' if current else 'OFF'}</code>"
                    f"</blockquote>",
                )

            if chat_id not in active:
                return await premium_reply(
                    message,
                    ":loop: <b>Loop</b>\n\n"
                    "<blockquote>"
                    "There is no active stream in this chat.\n\n"
                    ":music: Start one with /play first."
                    "</blockquote>",
                )

            state = arg == "on"
            loop_enabled[chat_id] = state
            track = active.get(chat_id)

            await action_log(f"Loop {'On' if state else 'Off'}", message)
            await premium_reply(
                message,
                f":loop: <b>Loop {'Enabled' if state else 'Disabled'}</b>\n\n"
                f"<blockquote>"
                f":music: <b>Track:</b> {get_title(track)}\n"
                f":signal: <b>Status:</b> <code>{'ON — current track will repeat' if state else 'OFF — queue will advance normally'}</code>\n\n"
                f"{'Use /loop off to return to normal playback.' if state else 'The queue will now continue normally.'}"
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Loop", e)
            await premium_reply(
                message,
                f":error: <b>Loop Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def volume(client, message):
        try:
            chat_id = message.chat.id

            if len(message.command) < 2 or not message.command[1].isdigit():
                return await premium_reply(
                    message,
                    ":volume: <b>Volume Usage</b>\n\n"
                    "<blockquote>:volume: <b>/volume</b> <code>[1-200]</code></blockquote>",
                )

            vol = int(message.command[1])

            if not 1 <= vol <= 200:
                return await premium_reply(
                    message,
                    ":warning: <b>Invalid Volume</b>\n\n"
                    "<blockquote>Volume must be between <code>1</code> and <code>200</code>.</blockquote>",
                )

            if chat_id not in active:
                return await premium_reply(
                    message,
                    ":volume: <b>Volume</b>\n\n"
                    "<blockquote>There is no active stream in this chat.</blockquote>",
                )

            await call.change_volume_call(chat_id, vol)
            await action_log(f"Volume -> {vol}", message)

            filled = int(vol / 200 * 10)
            empty = 10 - filled
            bar = "●" * filled + "○" * empty

            await premium_reply(
                message,
                f":volume: <b>Volume Updated</b>\n\n"
                f"<blockquote>"
                f":signal: <b>Level:</b> <code>{bar}</code> <code>{vol}%</code>\n\n"
                f"Playback volume updated."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Volume", e)
            await premium_reply(
                message,
                f":error: <b>Volume Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def seek(client, message):
        await premium_reply(
            message,
            ":warning: <b>Seek Unavailable</b>\n\n"
            "<blockquote>"
            "This PyTgCalls version does not support stream seeking.\n\n"
            ":skip: Use /skip or /play again to control playback."
            "</blockquote>",
        )

    async def clearqueue(client, message):
        try:
            chat_id = message.chat.id
            items = queue.list(chat_id)

            if not items:
                return await premium_reply(
                    message,
                    ":delete: <b>Clear Queue</b>\n\n"
                    "<blockquote>"
                    "The queue is already empty.\n\n"
                    ":music: Use /play to add tracks."
                    "</blockquote>",
                )

            count = len(items)
            queue.clear(chat_id)

            await action_log("Clear Queue", message)
            await premium_reply(
                message,
                f":delete: <b>Queue Cleared</b>\n\n"
                f"<blockquote>"
                f":queue: <b>Tracks Removed:</b> <code>{count}</code>\n\n"
                f"Current track will continue playing."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("ClearQueue", e)
            await premium_reply(
                message,
                f":error: <b>Clear Queue Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def remove(client, message):
        try:
            chat_id = message.chat.id

            if len(message.command) < 2 or not message.command[1].isdigit():
                return await premium_reply(
                    message,
                    ":delete: <b>Remove Usage</b>\n\n"
                    "<blockquote>"
                    ":delete: <b>/remove</b> <code>[position]</code>\n\n"
                    ":queue: Use /queue to see position numbers."
                    "</blockquote>",
                )

            pos = int(message.command[1])
            items = queue.list(chat_id)

            if not items:
                return await premium_reply(
                    message,
                    ":delete: <b>Remove</b>\n\n"
                    "<blockquote>The queue is empty.</blockquote>",
                )

            if not 1 <= pos <= len(items):
                return await premium_reply(
                    message,
                    f":warning: <b>Invalid Position</b>\n\n"
                    f"<blockquote>Queue has <code>{len(items)}</code> track(s).</blockquote>",
                )

            removed = items.pop(pos - 1)
            queue._queue[chat_id] = items

            await action_log(f"Remove #{pos}", message)
            await premium_reply(
                message,
                f":delete: <b>Track Removed</b>\n\n"
                f"<blockquote>"
                f":queue: <b>Position:</b> <code>#{pos}</code>\n"
                f":music: <b>Title:</b> {get_title(removed)}\n\n"
                f":success: <code>{len(items)}</code> track(s) remaining."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Remove", e)
            await premium_reply(
                message,
                f":error: <b>Remove Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(shuffle, filters.command("shuffle")))
    app.add_handler(MessageHandler(loop, filters.command("loop")))
    app.add_handler(MessageHandler(volume, filters.command("volume")))
    app.add_handler(MessageHandler(seek, filters.command("seek")))
    app.add_handler(MessageHandler(clearqueue, filters.command(["clearqueue", "cq"])))
    app.add_handler(MessageHandler(remove, filters.command(["remove", "rm"])))