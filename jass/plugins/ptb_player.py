# ==========================================================
# JassMusic - PTB Premium Player Callbacks
# Copyright (c) 2026 Jass
# ==========================================================

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes

from jass.helpers.premium_ptb import render
from jass.helpers.buttons import player_close_button_ptb
from jass.core.player import skip_track, stop_track
from jass.core.logger import error_log


def register_ptb_player(application, pyro_app, call):

    async def edit_stopped(query):
        text = render(":stop: <b>Stream Stopped</b>")

        try:
            await query.edit_message_caption(
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=player_close_button_ptb(),
            )
            return
        except Exception:
            pass

        try:
            await query.edit_message_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=player_close_button_ptb(),
                disable_web_page_preview=True,
            )
        except Exception as e:
            await error_log("PTB Player Stop Edit", e)

    async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        if not query or not query.message:
            return

        data = query.data
        chat_id = query.message.chat.id

        try:
            if data == "skip":
                await skip_track(pyro_app, call, chat_id, None)
                await query.answer("Track skipped")

            elif data == "stop":
                await stop_track(call, chat_id)
                await edit_stopped(query)
                await query.answer("Stopped")

            elif data == "pause":
                await call.pause(chat_id)
                await query.answer("Playback paused")

            elif data == "resume":
                await call.resume(chat_id)
                await query.answer("Playback resumed")

            elif data == "replay":
                await query.answer("Replay coming soon", show_alert=False)

            elif data == "delete_player":
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await query.answer()

            elif data in ("progress", "status"):
                await query.answer("Streaming is active", show_alert=False)

            else:
                await query.answer()

        except Exception as e:
            await error_log("PTB Player Callback", e)
            try:
                await query.answer("Something went wrong", show_alert=True)
            except Exception:
                pass

    application.add_handler(
        CallbackQueryHandler(
            cb,
            pattern=r"^(skip|stop|pause|resume|replay|delete_player|progress|status)$",
        )
    )