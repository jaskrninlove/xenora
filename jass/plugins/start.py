# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

import os
import random
import time
from pathlib import Path

import psutil
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from jass.helpers.premium_ptb import render
from jass.helpers.buttons import start_buttons, help_buttons, group_start_buttons
from jass.config import config
from jass.core.database import db
from jass.core.player import START_TIME, active
from jass.core.logger import start_command_log, action_log, error_log


HELP = {
    "main": """<blockquote><b>:music: Help Center</b></blockquote>

Welcome to the command reference. Browse the categories below to discover everything at your fingertips.

<b>:queue: Available Sections</b>
<blockquote>
:play: <b>Play</b> — Music & voice chat playback controls
:settings: <b>Admin</b> — Group permission & access management
:owner: <b>Owner</b> — Restricted bot management tools
:tools: <b>Tools</b> — Diagnostics, ping & uptime
:download: <b>Download</b> — Save audio & video from Telegram
:settings: <b>Settings</b> — Customise bot behaviour per group

</blockquote>
<blockquote>Select a section below to explore its commands in detail.</blockquote>""",

    "play": """<b>:music: Music Playback Commands</b>

<blockquote>:play: <b>/play</b> <code>[song name or URL]</code>
Stream any track by name or direct link instantly into the voice chat.

:video: <b>/vplay</b> <code>[video name or URL]</code>
Play video content directly in the voice channel with high-quality audio.

:skip: <b>/skip</b>
Skip the current track and automatically load the next one in queue.

:queue: <b>/queue</b>
Display the full list of upcoming tracks queued for playback.

:shuffle: <b>/shuffle</b>
Randomly reorder all tracks currently waiting in the queue.

:loop: <b>/loop</b> <code>[on / off]</code>
Toggle repeat mode for the current track or the entire queue.

:volume: <b>/volume</b> <code>[1–200]</code>
Adjust playback volume to your preferred level in the voice chat.

:search: <b>/seek</b> <code>[seconds]</code>
Jump to a specific position in the currently playing track.

:stop: <b>/end</b>
Stop playback entirely and clear the active queue, ending the session.</blockquote>

<blockquote>Delivering crystal-clear audio streaming across your voice chats.</blockquote>""",

    "admin": """<b>:settings: Admin Control Commands</b>

<blockquote>:success: <b>/auth</b> <code>[@user]</code>
Grant a user permission to control music playback in this group.

:error: <b>/unauth</b> <code>[@user]</code>
Revoke playback permissions from a previously authorized user.

:profile: <b>/authlist</b>
View all users currently authorised to manage playback in this group.

:error: <b>/blacklistchat</b>
Block the bot from functioning in the current group entirely.

:success: <b>/whitelistchat</b>
Re-enable the bot in a previously blacklisted group.

:pause: <b>/pause</b>
Temporarily pause the currently playing track in the voice chat.

:play: <b>/resume</b>
Resume playback from where it was paused.

:qqqq: <b>/clearqueue</b>
Remove all tracks from the queue without stopping current playback.

:delete: <b>/remove</b> <code>[position]</code>
Delete a specific track from the queue by its position number.</blockquote>

<blockquote>Manage permissions, access, and playback with precision.</blockquote>""",
    "owner": """<b>:owner: Owner Panel — Restricted Access</b>

<blockquote>:updates: <b>/broadcast</b>
Reply to any message to send it to all users in the database. Supports all media types and inline buttons; the forward header is stripped automatically.

:stats: <b>/stats</b>
View a full breakdown of bot statistics including users, plays, active streams, CPU, and RAM usage.

:receipt: <b>/logger</b> <code>[on / off]</code>
Toggle live command logging to the designated log channel on or off.

:active: <b>/activevc</b>
List all voice chats where the bot is currently active and streaming.

:error: <b>/gban</b> <code>[@user]</code>
Globally ban a user from accessing the bot across all groups.

:success: <b>/ungban</b> <code>[@user]</code>
Lift a global ban, restoring the user's access to the bot.

:settings: <b>/maintenance</b> <code>[on / off]</code>
Put the bot into maintenance mode, restricting usage to the owner only.</blockquote>

<blockquote>Advanced tools reserved exclusively for the bot owner.</blockquote>""",

    "tools": """<b>:tools: Utility & Diagnostics Commands</b>

<blockquote>:ping: <b>/ping</b>
Measure the bot's current response latency and confirm it's online.

:signal: <b>/uptime</b>
Check how long the bot has been continuously running since its last restart.

:stats: <b>/health</b>
View a full system report — CPU load, RAM usage, active streams, and connectivity status.

:key: <b>/id</b>
Retrieve the Telegram ID of yourself, a replied-to user, or the current chat.

:rocket: <b>/speed</b>
Run a live network speed test and display download and upload results.</blockquote>

<blockquote>Monitor performance and ensure everything is running at its best.</blockquote>""",

    "download": """<b>:download: Download Commands</b>

<blockquote>:music: <b>/song</b> <code>[song name or URL]</code>
Download and send the audio file of any track directly to your chat.

:video: <b>/video</b> <code>[video name or URL]</code>
Download and send the video file of any YouTube or supported link.

:thumb: <b>/thumbnail</b> <code>[YouTube URL]</code>
Fetch and send the full-resolution thumbnail of any YouTube video.</blockquote>

<blockquote>All downloads are sent directly into your Telegram chat.</blockquote>""",

    "settings": """<b>:settings: Settings & Configuration</b>

<blockquote>:play: <b>/setplaymode</b> <code>[direct / queue]</code>
Choose whether new songs play immediately or are added to the queue.

:signal: <b>/setstream</b> <code>[audio / video]</code>
Set the default stream type for playback in this group's voice chat.

:language: <b>/setlang</b> <code>[language code]</code>
Change the bot's response language for this group (e.g. <code>en</code>, <code>hi</code>).

:settings: <b>/settings</b>
View and manage all active configuration options for this group.</blockquote>

<blockquote>Customise your bot to match your group's preferences.</blockquote>""",
}


def uptime():
    seconds = int(time.time() - START_TIME)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs}s"


BASE_DIR = Path("assets")


def get_random_start_media():
    gifs_dir = BASE_DIR / "gifs"
    images_dir = BASE_DIR / "images"

    gifs = []
    images = []

    if gifs_dir.exists():
        gifs = [
            str(gifs_dir / f)
            for f in os.listdir(gifs_dir)
            if f.lower().endswith((".gif", ".mp4"))
        ]

    if images_dir.exists():
        images = [
            str(images_dir / f)
            for f in os.listdir(images_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

    if gifs:
        return random.choice(gifs), "gif"

    if images:
        return random.choice(images), "image"

    return None, None

def start_caption(mention: str, bot_name: str):
    return f"""<blockquote><b>:music: {bot_name}</b></blockquote>

Hey <b>{mention}</b>, welcome.

<i>I'm your premium voice chat music companion — built for smooth playback, clean controls, crystal-clear streaming and beautiful group music sessions.</i>

<blockquote>:play: Stream songs in voice chat
:queue: Manage queues smoothly
:download: Download songs, videos and thumbnails
:settings: Customise playback for your group</blockquote>

<blockquote>Use the buttons below to get started.</blockquote>"""


def group_start_caption(bot_name: str):
    return f"""<blockquote><b>:bot: {bot_name}</b></blockquote>

:success: <b>{bot_name} is alive baby.</b>

<b>:active: Ready to stream music in voice chats.</b>"""


async def send_start_media(message, text: str, buttons):
    media, media_type = get_random_start_media()

    if media:
        try:
            if media_type == "gif":
                await message.reply_animation(
                    animation=media,
                    caption=render(text),
                    parse_mode=ParseMode.HTML,
                    reply_markup=buttons,
                )
            else:
                await message.reply_photo(
                    photo=media,
                    caption=render(text),
                    parse_mode=ParseMode.HTML,
                    reply_markup=buttons,
                )
            return True
        except Exception:
            pass

    if config.START_IMG:
        try:
            await message.reply_photo(
                photo=config.START_IMG,
                caption=render(text),
                parse_mode=ParseMode.HTML,
                reply_markup=buttons,
            )
            return True
        except Exception:
            pass

    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        bot = await context.bot.get_me()

        if user:
            try:
                await db.add_user(user.id, user.first_name or "")
            except Exception:
                pass

        if chat.type in ("group", "supergroup"):
            try:
                await db.add_chat(chat.id, chat.title or "")
            except Exception:
                pass

        bot_name = bot.first_name or "Music Bot"
        bot_username = bot.username
        mention = user.mention_html() if user else "there"

        if chat.type in ("group", "supergroup"):
            text = group_start_caption(bot_name)
            buttons = group_start_buttons(bot_username)
        else:
            text = start_caption(mention, bot_name)
            buttons = start_buttons(bot_username)

        sent = await send_start_media(message, text, buttons)

        if not sent:
            await message.reply_text(
                render(text),
                parse_mode=ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True,
            )

    except Exception as e:
        try:
            await error_log("PTB Start Command", e)
        except Exception:
            pass


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message

        t = time.perf_counter()
        m = await message.reply_text(
            render(":ping: <i>Measuring latency, please wait...</i>"),
            parse_mode=ParseMode.HTML,
        )
        ms = (time.perf_counter() - t) * 1000

        try:
            await action_log("PTB Ping Command", message)
        except Exception:
            pass

        status = ":success: Excellent" if ms < 100 else ":warning: Moderate" if ms < 300 else ":error: High"

        await m.edit_text(
            render(
                f"""<blockquote><b>:ping: Network Diagnostics</b></blockquote>

:signal: <b>Response Latency :</b> <code>{ms:.2f} ms</code>  {status}
:rocket: <b>Session Uptime :</b> <code>{uptime()}</code>
:active: <b>Active Streams :</b> <code>{len(active)}</code>

<blockquote>All systems are operational and running smoothly.</blockquote>"""
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        try:
            await error_log("PTB Ping Command", e)
        except Exception:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message

        s = await db.stats()

        try:
            await action_log("PTB Stats Command", message)
        except Exception:
            pass

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_used = ram.used // (1024 ** 2)
        ram_total = ram.total // (1024 ** 2)

        await message.reply_text(
            render(
                f"""<blockquote><b>:stats: Bot Statistics — Overview</b></blockquote>

<b>:profile: Community</b>
:profile: <b>Total Users :</b> <code>{s.get("users", 0)}</code>
:chat: <b>Total Groups :</b> <code>{s.get("groups", 0)}</code>
:music: <b>Total Plays :</b> <code>{s.get("plays", 0)}</code>
:active: <b>Active Voice Chats :</b> <code>{len(active)}</code>

<b>:stats: System Resources</b>
:tools: <b>CPU Usage :</b> <code>{cpu}%</code>
:battery: <b>RAM Usage :</b> <code>{ram_used} MB / {ram_total} MB</code>
:rocket: <b>Session Uptime :</b> <code>{uptime()}</code>

<blockquote>Keeping the music alive across Telegram, one stream at a time.</blockquote>"""
            ),
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        try:
            await error_log("PTB Stats Command", e)
        except Exception:
            pass


async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        bot = await context.bot.get_me()
        bot_name = bot.first_name or "Music Bot"
        bot_username = bot.username

        if query.data == "home":
            text = start_caption(query.from_user.mention_html(), bot_name)
            buttons = start_buttons(bot_username)

        elif query.data.startswith("help"):
            page = query.data.split(":", 1)[1]
            text = HELP.get(page, HELP["main"])
            buttons = help_buttons(page)

        elif query.data == "stats":
            s = await db.stats()
            await query.answer(
                f'Users: {s.get("users", 0)} | Plays: {s.get("plays", 0)} | Active: {len(active)}',
                show_alert=True,
            )
            return

        else:
            return

        is_media = bool(query.message.photo or query.message.animation)

        try:
            if is_media:
                await query.edit_message_caption(
                    caption=render(text),
                    parse_mode=ParseMode.HTML,
                    reply_markup=buttons,
                )
            else:
                await query.edit_message_text(
                    render(text),
                    parse_mode=ParseMode.HTML,
                    reply_markup=buttons,
                    disable_web_page_preview=True,
                )
        except Exception as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise

    except Exception as e:
        try:
            await error_log("PTB Callback Start/Help", e)
        except Exception:
            pass

        try:
            await update.callback_query.answer("Something went wrong", show_alert=True)
        except Exception:
            pass


def register_ptb(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["ping", "uptime", "health"], ping))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(cb, pattern=r"^(home|stats|help:.*)$"))