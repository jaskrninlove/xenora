# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import asyncio
import time

from pyrogram.errors import UserAlreadyParticipant
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

from jass import assistant
from .queue import queue
from .youtube import get_track
from .logger import error_log
from ..helpers.buttons import player_buttons
from ..helpers.buttons import player_buttons, player_close_button

START_TIME = time.time()

loop_enabled = {}
active = {}
player_messages = {}
progress_tasks = {}
end_tasks = {}
track_tokens = {}


def format_duration(seconds: int):
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


def progress_bar(current: int, total: int):
    total = int(total or 0)
    current = int(current or 0)

    if total <= 0:
        return "00:00 ◉────── 00:00"

    size = 6
    current = min(current, total)
    filled = int(size * current / total)

    bar = "━" * filled + "◉" + "─" * max(0, size - filled)

    return f"{format_duration(current)} {bar} {format_duration(total)}"


def stream(track):
    if getattr(track, "is_video", False):
        return MediaStream(
            track.url,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
        )

    return MediaStream(
        track.url,
        audio_parameters=AudioQuality.HIGH,
    )


async def ensure_assistant_joined(client, message):
    chat_id = message.chat.id

    try:
        await assistant.get_chat(chat_id)
        return True
    except Exception:
        pass

    try:
        invite = await client.export_chat_invite_link(chat_id)

        try:
            await assistant.join_chat(invite)
        except UserAlreadyParticipant:
            pass

        return True

    except Exception as e:
        await message.reply_text(
            f"""<blockquote><b>⚠️ Assistant Required</b></blockquote>

Bot tried to invite assistant automatically but failed.

<b>Give bot admin permissions:</b>
Invite Users + Manage Video Chats

<b>Error:</b> <code>{e}</code>"""
        )
        return False

def short_title(title: str, limit: int = 38):
    if not title:
        return "Unknown Track"

    if len(title) > limit:
        return title[:limit] + "..."
    return title

def play_caption(track, requested_by):
    title = short_title(track.title)

    if getattr(track, "webpage_url", None):
        title = f'<a href="{track.webpage_url}">{title}</a>'

    return f"""<blockquote><b>⋆.˚Started Streaming₊*･ﾟ</b></blockquote>

‣ <b>Title :</b> {title}
‣ <b>Duration :</b> {format_duration(track.duration)} ᴍɪɴᴜᴛᴇs
‣ <b>Requested By :</b> {requested_by} .

⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖
"""


def queue_caption(track, requested_by, pos: int):
    title = short_title(track.title)

    if getattr(track, "webpage_url", None):
        title = f'<a href="{track.webpage_url}">{title}</a>'

    return f"""<blockquote><b>𐙚 Added to Queue At #{pos}</b></blockquote>

▸ <b>Title :</b> {title}
▸ <b>Duration :</b> {format_duration(track.duration)} Minutes
▸ <b>Requested By :</b> {requested_by} .

⊹ ࣪ ﹏𓊝﹏𓂁﹏⊹ ࣪ ˖
"""


async def stop_progress(chat_id: int):
    task = progress_tasks.pop(chat_id, None)
    if task:
        task.cancel()


async def stop_end_timer(chat_id: int):
    task = end_tasks.pop(chat_id, None)
    if task:
        task.cancel()


async def progress_worker(chat_id: int, track, token: float):
    start = time.time()

    while chat_id in active and track_tokens.get(chat_id) == token:
        try:
            current = int(time.time() - start)

            if current >= int(track.duration or 0):
                break

            msg = player_messages.get(chat_id)
            if msg:
                await msg.edit_reply_markup(
                    reply_markup=player_buttons(progress_bar(current, track.duration))
                )

            await asyncio.sleep(20)

        except asyncio.CancelledError:
            break

        except Exception:
            await asyncio.sleep(20)


async def auto_next_worker(client, call, chat_id: int, track, token: float):
    try:
        duration = int(track.duration or 0)

        if duration <= 0:
            duration = 300

        await asyncio.sleep(duration + 8)

        if track_tokens.get(chat_id) != token:
            return

        if chat_id not in active:
            return

        await play_next_from_queue(client, call, chat_id, None)

    except asyncio.CancelledError:
        pass

    except Exception as e:
        await error_log("Auto Next Worker", e)


async def play_next_from_queue(client, call, chat_id: int, message=None):
    if loop_enabled.get(chat_id):
        current_track = active.get(chat_id)

        if current_track:
            await call.play(chat_id, stream(current_track))
            await start_track_tasks(client, call, chat_id, current_track)
            return

    next_track = queue.pop(chat_id)

    if not next_track:
        await stop_track(call, chat_id)

        if message:
            await message.reply_text(
                """<blockquote><b>𐙚 Stream Ended 𐙚</b></blockquote>
  |
└ <b>By :</b> {user} .🕸️

<blockquote><b>𐙚 No more queued tracks in music, leaving videochat.✧.*</b></blockquote>""".format(
                    user=message.from_user.mention if message.from_user else "Unknown"
                ),
                reply_markup=player_close_button(),
            )

        return

    await call.play(chat_id, stream(next_track))
    active[chat_id] = next_track

    if message:
        await send_player_ui(message, next_track)
    else:
        old_msg = player_messages.get(chat_id)

        if old_msg:
            caption = play_caption(next_track, "ᴀᴜᴛᴏ ᴘʟᴀʏᴇʀ")
            new_msg = await send_card(old_msg, caption, next_track, buttons=True)
            player_messages[chat_id] = new_msg

    await start_track_tasks(client, call, chat_id, next_track)

async def send_card(message, caption, track, buttons=True):
    reply_markup = player_buttons(progress_bar(0, track.duration)) if buttons else None
    thumb = getattr(track, "thumbnail", None) or getattr(track, "thumb", None)

    if thumb:
        try:
            return await message.reply_photo(
                photo=thumb,
                caption=caption,
                reply_markup=reply_markup,
            )
        except Exception:
            pass

    return await message.reply_text(
        caption,
        reply_markup=reply_markup,
    )


async def start_track_tasks(client, call, chat_id: int, track):
    token = time.time()
    track_tokens[chat_id] = token

    await stop_progress(chat_id)
    await stop_end_timer(chat_id)

    progress_tasks[chat_id] = asyncio.create_task(
        progress_worker(chat_id, track, token)
    )
    end_tasks[chat_id] = asyncio.create_task(
        auto_next_worker(client, call, chat_id, track, token)
    )


async def send_player_ui(message, track):
    requested_by = message.from_user.mention if message and message.from_user else "Unknown"
    caption = play_caption(track, requested_by)

    msg = await send_card(message, caption, track, buttons=True)
    player_messages[message.chat.id] = msg
    return msg


async def send_queue_ui(message, track, pos: int):
    requested_by = message.from_user.mention if message.from_user else "Unknown"
    caption = queue_caption(track, requested_by, pos)
    return await send_card(message, caption, track, buttons=True)


async def play_query(client, call, message, query: str, video: bool = False):
    if not await ensure_assistant_joined(client, message):
        return

    chat_id = message.chat.id
    track = await get_track(query, video=video)
    track.is_video = video

    if chat_id in active:
        pos = queue.add(chat_id, track)
        return await send_queue_ui(message, track, pos)

    try:

       await call.play(chat_id, stream(track))

    except Exception as e:
       err = str(e)

       if (
        "CHAT_ADMIN_REQUIRED" in err
        or "CreateGroupCall" in err
        or "phone.CreateGroupCall" in err
       ):
        return await message.reply_text(
            """<blockquote><b>𐙚 The Stage Is Empty 𐙚</b></blockquote>

The music longs to play, but no voice chat is currently active in this group. 🎭

°❀⋆ Start a voice chat first.
°❀⋆ Then send /play again.

<blockquote><b>♫ The moment the curtains rise, the melody shall begin. ✧.*</b></blockquote>"""
        )

       raise

    active[chat_id] = track
    await send_player_ui(message, track)
    await start_track_tasks(client, call, chat_id, track)


async def play_next_from_queue(client, call, chat_id: int, message=None):
    if loop_enabled.get(chat_id):
        current_track = active.get(chat_id)

        if current_track:
           await call.play(chat_id, stream(current_track))
           await start_track_tasks(client, call, chat_id, current_track)
           return
    
    next_track = queue.pop(chat_id)

    if not next_track:
        await stop_track(call, chat_id)

        if message:
            await message.reply_text(
                """<blockquote><b>𐙚 Stream Ended 𐙚</b></blockquote>
  |                
└ <b>By :</b> {user} .🕸️

<blockquote><b>𐙚 No more queued tracks in music, leaving videochat.✧.*</b></blockquote>""".format(
                    user=message.from_user.mention if message.from_user else "Unknown"
                ),
                reply_markup=player_close_button(),
            )

        return

    await call.play(chat_id, stream(next_track))
    active[chat_id] = next_track

    if message:
        await send_player_ui(message, next_track)
    else:
        old_msg = player_messages.get(chat_id)
        if old_msg:
            caption = play_caption(next_track, "ᴀᴜᴛᴏ ᴘʟᴀʏᴇʀ")
            new_msg = await send_card(old_msg, caption, next_track, buttons=True)
            player_messages[chat_id] = new_msg

    await start_track_tasks(client, call, chat_id, next_track)


async def skip_track(client, call, chat_id: int, message=None):
    await play_next_from_queue(client, call, chat_id, message)


async def stop_track(call, chat_id: int):
    queue.clear(chat_id)
    active.pop(chat_id, None)
    player_messages.pop(chat_id, None)
    track_tokens.pop(chat_id, None)

    await stop_progress(chat_id)
    await stop_end_timer(chat_id)

    try:
     await call.leave_call(chat_id)
    except Exception:
     pass

    try:
     await call.leave_group_call(chat_id)
    except Exception:
     pass

    try:
     await assistant.leave_chat(chat_id)
    except Exception:
     pass


def register_end_handler(app, call):
    return