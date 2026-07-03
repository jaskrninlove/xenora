# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from ..core.player import (
    play_query,
    skip_track,
    stop_track,
    active,
    register_end_handler,
)
from ..core.queue import queue
from ..core.logger import play_command_log, action_log, error_log
from ..helpers.buttons import player_close_button
from ..helpers.premium import render
from pyrogram.enums import ParseMode

LOADING_STICKER = ""  # add real sticker file_id here


async def premium_reply(message, text: str, **kwargs):
    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def premium_edit(message, text: str, **kwargs):
    return await message.edit_text(
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


def register(app, call):
    register_end_handler(app, call)

    async def play(client, message):
        if len(message.command) < 2:
            return await premium_reply(
                message,
                ":music: <b>Play Usage</b>\n\n"
                "<blockquote>"
                ":play: <b>/play</b> <code>[song name or link]</code>\n"
                ":video: <b>/vplay</b> <code>[video name or link]</code>\n\n"
                "Send a song name or link to start streaming."
                "</blockquote>",
            )

        query = " ".join(message.command[1:])

        try:
            me = await client.get_me()
            member = await message.chat.get_member(me.id)

            if member.privileges and member.privileges.can_delete_messages:
                await message.delete()

        except Exception:
            pass

        loading = None
        try:
            if LOADING_STICKER:
                loading = await message.reply_sticker(LOADING_STICKER)
            else:
                loading = await premium_reply(
                    message,
                    ":rocket: <b>Preparing Stream</b>\n\n"
                    f"<blockquote>:search: <b>Query:</b> <code>{query}</code>\n"
                    ":music: Searching and loading your track...</blockquote>",
                )
        except Exception:
            loading = None

        try:
            await play_command_log(message, query)
            is_video = message.command[0].lower() == "vplay"
            await play_query(client, call, message, query, video=is_video)

            if loading:
                await loading.delete()

        except Exception as e:
            await error_log("Play Command", e)

            if loading:
                try:
                    await loading.delete()
                except Exception:
                    pass

            await premium_reply(
                message,
                f":error: <b>Play Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def skip(client, message):
        try:
            await action_log("Skip Command", message)
            await skip_track(client, call, message.chat.id, message)
        except Exception as e:
            await error_log("Skip Command", e)
            await premium_reply(
                message,
                f":error: <b>Skip Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def end(client, message):
        try:
            await action_log("End Command", message)
            await stop_track(call, message.chat.id)

            user = message.from_user.mention if message.from_user else "Unknown"

            await premium_reply(
                message,
                f":stop: <b>Stream Stopped</b>\n\n"
                f"<blockquote>"
                f":profile: <b>Stopped By:</b> {user}\n\n"
                f":music: Music playback has been terminated and the assistant has left the voice chat."
                f"</blockquote>",
                reply_markup=player_close_button(),
            )

        except Exception as e:
            await error_log("End Command", e)
            await premium_reply(
                message,
                f":error: <b>Stop Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def q(client, message):
        try:
            items = queue.list(message.chat.id)

            if not items:
                return await premium_reply(
                    message,
                    ":queue: <b>Queue Empty</b>\n\n"
                    "<blockquote>No tracks are waiting in the queue.</blockquote>",
                )

            lines = [
                f":music: <b>{i + 1}.</b> {getattr(t, 'title', 'Unknown Track')}"
                for i, t in enumerate(items)
            ]

            await premium_reply(
                message,
                ":queue: <b>Current Queue</b>\n\n"
                "<blockquote>"
                + "\n".join(lines)
                + "</blockquote>",
            )

        except Exception as e:
            await error_log("Queue Command", e)
            await premium_reply(
                message,
                f":error: <b>Queue Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def activevc(client, message):
        try:
            await action_log("Active VC Command", message)

            if not active:
                return await premium_reply(
                    message,
                    ":active: <b>Active Voice Chats</b>\n\n"
                    "<blockquote>No active voice chats right now.</blockquote>",
                )

            text = "\n".join(f":music: <code>{chat_id}</code>" for chat_id in active.keys())

            await premium_reply(
                message,
                ":active: <b>Active Voice Chats</b>\n\n"
                f"<blockquote>{text}</blockquote>",
            )

        except Exception as e:
            await error_log("ActiveVC Command", e)
            await premium_reply(
                message,
                f":error: <b>ActiveVC Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    async def cb(client, cq):
        try:
            if cq.data == "skip":
                await skip_track(client, call, cq.message.chat.id, cq.message)
                await cq.answer("Skipped")

            elif cq.data == "stop":
                await stop_track(call, cq.message.chat.id)
                await premium_edit(
                    cq.message,
                    ":stop: <b>Stream Stopped</b>",
                    reply_markup=player_close_button(),
                )
                await cq.answer("Stopped")

            elif cq.data == "pause":
                await call.pause(cq.message.chat.id)
                await cq.answer("Paused")

            elif cq.data == "resume":
                await call.resume(cq.message.chat.id)
                await cq.answer("Resumed")

            elif cq.data == "replay":
                await cq.answer("Replay coming soon", show_alert=False)

            elif cq.data == "delete_player":
                await cq.message.delete()

            elif cq.data in ["progress", "status"]:
                await cq.answer("Streaming is active", show_alert=False)

            else:
                await cq.answer()

        except Exception as e:
            await error_log("Player Callback", e)
            await cq.answer("Something went wrong", show_alert=True)

    app.add_handler(MessageHandler(play, filters.command(["play", "vplay"])))
    app.add_handler(MessageHandler(skip, filters.command("skip")))
    app.add_handler(MessageHandler(end, filters.command(["end", "stop"])))
    app.add_handler(MessageHandler(q, filters.command("queue")))
    app.add_handler(MessageHandler(activevc, filters.command(["activevc", "active"])))
    app.add_handler(
        CallbackQueryHandler(
            cb,
            filters.regex(
                r"^(skip|stop|pause|resume|replay|delete_player|progress|status)$"
            ),
        )
    )