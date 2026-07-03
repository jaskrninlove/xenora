# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

import asyncio
import time
import socket
import urllib.request
from pyrogram.enums import ParseMode
from pyrogram import filters
from pyrogram.handlers import MessageHandler

from ..core.logger import action_log, error_log
from ..helpers.premium import render


async def premium_reply(message, text: str):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
    )


async def premium_edit(message, text: str):
    return await message.edit_text(
        render(text),
        parse_mode=ParseMode.HTML,
    )


def register(app, call):

    async def id_cmd(client, message):
        try:
            await action_log("ID Command", message)

            lines = []

            if message.reply_to_message and message.reply_to_message.from_user:
                user = message.reply_to_message.from_user
                lines.append(
                    f":profile: <b>Replied User</b>\n"
                    f":profile: <b>Name:</b> {user.mention}\n"
                    f":key: <b>ID:</b> <code>{user.id}</code>\n"
                    f":mail: <b>Username:</b> {'@' + user.username if user.username else 'None'}"
                )

            if message.from_user:
                user = message.from_user
                lines.append(
                    f":profile: <b>You</b>\n"
                    f":profile: <b>Name:</b> {user.mention}\n"
                    f":key: <b>ID:</b> <code>{user.id}</code>\n"
                    f":mail: <b>Username:</b> {'@' + user.username if user.username else 'None'}"
                )

            chat = message.chat
            chat_type = getattr(chat.type, "name", str(chat.type)).lower().replace("_", " ")

            lines.append(
                f":chat: <b>Chat</b>\n"
                f":chat: <b>Title:</b> {chat.title or chat.first_name or 'Unknown'}\n"
                f":key: <b>ID:</b> <code>{chat.id}</code>\n"
                f":settings: <b>Type:</b> <code>{chat_type}</code>"
            )

            me = await client.get_me()
            bot_name = me.first_name

            await premium_reply(
                message,
                ":key: <b>Telegram ID Info</b>\n\n"
                "<blockquote>"
                + "\n\n".join(lines)
                + f"\n\n:bot: {bot_name} — ID Lookup"
                "</blockquote>",
            )

        except Exception as e:
            await error_log("ID Command", e)
            await premium_reply(
                message,
                f":error: <b>ID Lookup Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def speed(client, message):
        try:
            await action_log("Speed Command", message)

            status = await premium_reply(
                message,
                ":rocket: <b>Speed Test</b>\n\n"
                "<blockquote>:signal: <b>Status:</b> <i>Running network test, please wait...</i></blockquote>",
            )

            test_url = "https://speed.cloudflare.com/__down?bytes=3000000"
            chunk_size = 65536

            def download_test():
                start = time.perf_counter()
                total = 0

                try:
                    with urllib.request.urlopen(test_url, timeout=15) as req:
                        while True:
                            chunk = req.read(chunk_size)
                            if not chunk:
                                break
                            total += len(chunk)
                except Exception:
                    pass

                elapsed = time.perf_counter() - start
                return total, elapsed

            def ping_test():
                try:
                    start = time.perf_counter()
                    sock = socket.create_connection(("1.1.1.1", 80), timeout=5)
                    sock.close()
                    return (time.perf_counter() - start) * 1000
                except Exception:
                    return 0.0

            dl_bytes, dl_secs = await asyncio.to_thread(download_test)
            ping_ms = await asyncio.to_thread(ping_test)

            dl_mbps = (dl_bytes * 8) / (dl_secs * 1_000_000) if dl_secs > 0 else 0

            def rate_speed(mbps: float):
                if mbps >= 100:
                    return ":success: Excellent"
                if mbps >= 50:
                    return ":star: Good"
                if mbps >= 10:
                    return ":warning: Moderate"
                return ":error: Poor"

            def rate_ping(ms: float):
                if ms <= 0:
                    return ":error: Failed"
                if ms < 50:
                    return ":success: Excellent"
                if ms < 150:
                    return ":star: Good"
                if ms < 300:
                    return ":warning: Moderate"
                return ":error: High"

            await premium_edit(
                status,
                f":rocket: <b>Network Speed Test</b>\n\n"
                f"<blockquote>"
                f":download: <b>Download:</b> <code>{dl_mbps:.2f} Mbps</code> {rate_speed(dl_mbps)}\n"
                f":ping: <b>Ping:</b> <code>{ping_ms:.1f} ms</code> {rate_ping(ping_ms)}\n\n"
                f"Test via Cloudflare — 3 MB sample."
                f"</blockquote>",
            )

        except Exception as e:
            await error_log("Speed Command", e)
            await premium_reply(
                message,
                f":error: <b>Speed Test Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(id_cmd, filters.command("id")))
    app.add_handler(MessageHandler(speed, filters.command("speed")))