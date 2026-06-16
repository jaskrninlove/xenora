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


LOADING_STICKER = ""  # add real sticker file_id here


def register(app, call):
    register_end_handler(app, call)

    async def play(client, message):
        if len(message.command) < 2:
            return await message.reply_text("Use: /play song name or link")

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
                loading = await message.reply_text("🦄")
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

            await message.reply_text(f"Play failed: <code>{e}</code>")

    async def skip(client, message):
        try:
            await action_log("⏭ Skip Command", message)
            await skip_track(client, call, message.chat.id, message)
        except Exception as e:
            await error_log("Skip Command", e)
            await message.reply_text(f"Skip failed: <code>{e}</code>")

    async def end(client, message):
        try:
            await action_log("⏹ End Command", message)
            await stop_track(call, message.chat.id)

            user = message.from_user.mention if message.from_user else "Unknown"

            await message.reply_text(
                f"""<blockquote><b>𐙚 Stream Stopped 𐙚</b></blockquote>
 |               
└ <b>By :</b> {user} .🕸️

<blockquote><b>♫ Music playback has been terminated and the assistant has left the voice chat.</b></blockquote>""",
                reply_markup=player_close_button(),
            )

        except Exception as e:
            await error_log("End Command", e)
            await message.reply_text(f"<b>Stop failed:</b>\n<code>{e}</code>")

    async def q(client, message):
        try:
            items = queue.list(message.chat.id)

            if not items:
                return await message.reply_text(
                    "<blockquote><b>𐙚 Queue Empty 𐙚</b></blockquote>\n\n"
                    "No tracks are waiting in the queue."
                )

            text = "<blockquote><b>𐙚 Current Queue 𐙚</b></blockquote>\n\n"
            text += "\n".join(
                f"❖ <b>{i + 1}.</b> {getattr(t, 'title', 'Unknown Track')}"
                for i, t in enumerate(items)
            )

            await message.reply_text(text)

        except Exception as e:
            await error_log("Queue Command", e)
            await message.reply_text(f"Queue failed: <code>{e}</code>")

    async def activevc(client, message):
        try:
            await action_log("🎧 Active VC Command", message)
            text = "\n".join(str(x) for x in active.keys()) or "No active VC."
            await message.reply_text(
                f"<blockquote><b>🎧 Active Voice Chats</b></blockquote>\n\n<code>{text}</code>"
            )
        except Exception as e:
            await error_log("ActiveVC Command", e)
            await message.reply_text(f"ActiveVC failed: <code>{e}</code>")

    async def cb(client, cq):
        try:
            if cq.data == "skip":
                await skip_track(client, call, cq.message.chat.id, cq.message)
                await cq.answer("Skipped")

            elif cq.data == "stop":
                await stop_track(call, cq.message.chat.id)
                await cq.message.edit_text(
                    "<blockquote><b>𐙚 Stream Stopped 𐙚</b></blockquote>",
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
                await cq.answer("Replay coming soon ♫", show_alert=False)

            elif cq.data == "delete_player":
                await cq.message.delete()

            elif cq.data in ["progress", "status"]:
                await cq.answer("Streaming is active ♫", show_alert=False)

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