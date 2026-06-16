# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import time
import psutil

from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from ..helpers.buttons import start_buttons, help_buttons, group_start_buttons
from ..config import config
from ..core.database import db
from ..core.player import START_TIME, active
from ..core.logger import start_command_log, action_log, error_log
import os
import random
from pathlib import Path

HELP = {
    "main": """<blockquote><b>🎧 Help Center</b></blockquote>

Welcome to the command reference. Browse the categories below to discover everything at your fingertips. ♫

<b>📂 Available Sections</b>
<blockquote>
❖ <b>Play</b> — Music & voice chat playback controls
❖ <b>Admin</b> — Group permission & access management
❖ <b>Owner</b> — Restricted bot management tools
❖ <b>Tools</b> — Diagnostics, ping & uptime
❖ <b>Download</b> — Save audio & video from Telegram
❖ <b>Settings</b> — Customise bot behaviour per group

</blockquote>
<b>Select a section below to explore its commands in detail.</b>""",

    "play": """<blockquote><b>🎵 Music Playback Commands</b></blockquote>

❖ <b>/play</b> <code>[song name or URL]</code>
┗ Stream any track by name or direct link instantly into the voice chat.

❖ <b>/vplay</b> <code>[video name or URL]</code>
┗ Play video content directly in the voice channel with high-quality audio.

❖ <b>/skip</b>
┗ Skip the current track and automatically load the next one in queue.

❖ <b>/queue</b>
┗ Display the full list of upcoming tracks queued for playback.

❖ <b>/shuffle</b>
┗ Randomly reorder all tracks currently waiting in the queue.

❖ <b>/loop</b> <code>[on / off]</code>
┗ Toggle repeat mode for the current track or the entire queue.

❖ <b>/volume</b> <code>[1–200]</code>
┗ Adjust playback volume to your preferred level in the voice chat.

❖ <b>/seek</b> <code>[seconds]</code>
┗ Jump to a specific position in the currently playing track.

❖ <b>/end</b>
┗ Stop playback entirely and clear the active queue, ending the session.

<blockquote>♫ Delivering crystal-clear audio streaming across your voice chats.</blockquote>""",

    "admin": """<blockquote><b>🛡 Admin Control Commands</b></blockquote>

❖ <b>/auth</b> <code>[@user]</code>
┗ Grant a user permission to control music playback in this group.

❖ <b>/unauth</b> <code>[@user]</code>
┗ Revoke playback permissions from a previously authorized user.

❖ <b>/authlist</b>
┗ View all users currently authorised to manage playback in this group.

❖ <b>/blacklistchat</b>
┗ Block the bot from functioning in the current group entirely.

❖ <b>/whitelistchat</b>
┗ Re-enable the bot in a previously blacklisted group.

❖ <b>/pause</b>
┗ Temporarily pause the currently playing track in the voice chat.

❖ <b>/resume</b>
┗ Resume playback from where it was paused.

❖ <b>/clearqueue</b>
┗ Remove all tracks from the queue without stopping current playback.

❖ <b>/remove</b> <code>[position]</code>
┗ Delete a specific track from the queue by its position number.

<blockquote>Manage permissions, access, and playback with precision.</blockquote>""",

    "owner": """<blockquote><b>👑 Owner Panel — Restricted Access</b></blockquote>

❖ <b>/broadcast</b>
┗ Reply to any message to send it to all users in the database. Supports all media types and inline buttons; the forward header is stripped automatically.

❖ <b>/stats</b>
┗ View a full breakdown of bot statistics including users, plays, active streams, CPU, and RAM usage.

❖ <b>/logger</b> <code>[on / off]</code>
┗ Toggle live command logging to the designated log channel on or off.

❖ <b>/activevc</b>
┗ List all voice chats where the bot is currently active and streaming.

❖ <b>/gban</b> <code>[@user]</code>
┗ Globally ban a user from accessing the bot across all groups.

❖ <b>/ungban</b> <code>[@user]</code>
┗ Lift a global ban, restoring the user's access to the bot.

❖ <b>/maintenance</b> <code>[on / off]</code>
┗ Put the bot into maintenance mode, restricting usage to the owner only.

<blockquote>Advanced tools reserved exclusively for the bot owner.</blockquote>""",

    "tools": """<blockquote><b>⚙ Utility & Diagnostics Commands</b></blockquote>

❖ <b>/ping</b>
┗ Measure the bot's current response latency and confirm it's online.

❖ <b>/uptime</b>
┗ Check how long the bot has been continuously running since its last restart.

❖ <b>/health</b>
┗ View a full system report — CPU load, RAM usage, active streams, and connectivity status.

❖ <b>/id</b>
┗ Retrieve the Telegram ID of yourself, a replied-to user, or the current chat.

❖ <b>/speed</b>
┗ Run a live network speed test and display download and upload results.

<blockquote>Monitor performance and ensure everything is running at its best.</blockquote>""",

    "download": """<blockquote><b>⬇️ Download Commands</b></blockquote>

❖ <b>/song</b> <code>[song name or URL]</code>
┗ Download and send the audio file of any track directly to your chat.

❖ <b>/video</b> <code>[video name or URL]</code>
┗ Download and send the video file of any YouTube or supported link.

❖ <b>/thumbnail</b> <code>[YouTube URL]</code>
┗ Fetch and send the full-resolution thumbnail of any YouTube video.

<blockquote>📥 All downloads are sent directly into your Telegram chat.</blockquote>""",

    "settings": """<blockquote><b>🔧 Settings & Configuration</b></blockquote>

❖ <b>/setplaymode</b> <code>[direct / queue]</code>
┗ Choose whether new songs play immediately or are added to the queue.

❖ <b>/setstream</b> <code>[audio / video]</code>
┗ Set the default stream type for playback in this group's voice chat.

❖ <b>/setlang</b> <code>[language code]</code>
┗ Change the bot's response language for this group (e.g. <code>en</code>, <code>hi</code>).

❖ <b>/settings</b>
┗ View and manage all active configuration options for this group.

<blockquote>🔧 Customise Your Bot to match your group's preferences.</blockquote>""",
}


def uptime():
    s = int(time.time() - START_TIME)
    h = s // 3600
    m = (s % 3600) // 60
    s_rem = s % 60
    return f"{h}h {m}m {s_rem}s"

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
    return f"""
Hey {mention}! 🥂,

I'm {bot_name} your personal voice chat music companion — built to keep every moment alive with music, rhythm, and crystal-clear streaming. Whether it's a chill late-night session, your favourite playlist, or a nonstop party in full swing — I've got you covered with powerful controls and high-quality audio. 🪼

<blockquote>Use the buttons below to get started or explore my commands. ♫</blockquote>"""

def group_start_caption(bot_name: str):
    return f"""<blockquote><b>❖ {bot_name}</b></blockquote>

❖ <b>{bot_name} is alive baby.</b>

<b>✯ Ready to stream music in voice chats.</b> 🎧"""

def register(app, call):
    async def start(client, message):
        try:
            if message.from_user:
                await db.add_user(
                    message.from_user.id,
                    message.from_user.first_name or "",
                )

            await start_command_log(message)

            if message.chat.type.name in ["GROUP", "SUPERGROUP"]:
                await db.add_chat(message.chat.id, message.chat.title or "")

            me = await client.get_me()
            bot_name = me.first_name or "Music Bot"
            mention = message.from_user.mention if message.from_user else "there"

            if message.chat.type.name in ["GROUP", "SUPERGROUP"]:
                text = group_start_caption(bot_name)
                buttons = group_start_buttons(me.username)
            else:
                text = start_caption(mention, bot_name)
                buttons = start_buttons(me.username)

            media, media_type = get_random_start_media()

            if media:
                try:
                    if media_type == "gif":
                        await message.reply_animation(
                            animation=media,
                            caption=text,
                            reply_markup=buttons,
                        )
                    else:
                        await message.reply_photo(
                            photo=media,
                            caption=text,
                            reply_markup=buttons,
                        )
                    return
                except Exception:
                    pass

            if config.START_IMG:
                try:
                    await message.reply_photo(
                        photo=config.START_IMG,
                        caption=text,
                        reply_markup=buttons,
                    )
                    return
                except Exception:
                    pass

            await message.reply_text(
                text,
                reply_markup=buttons,
            )

        except Exception as e:
            await error_log("Start Command", e)

    async def ping(client, message):
        try:
            t = time.perf_counter()
            m = await message.reply_text("⏳ <i>Measuring latency, please wait...</i>")
            ms = (time.perf_counter() - t) * 1000

            await action_log("🏓 Ping Command", message)

            status = "🟢 Excellent" if ms < 100 else "🟡 Moderate" if ms < 300 else "🔴 High"

            await m.edit_text(
                f"""<blockquote><b>🏓 Network Diagnostics</b></blockquote>

❖ <b>Response Latency :</b> <code>{ms:.2f} ms</code>  {status}
❖ <b>Session Uptime :</b> <code>{uptime()}</code>
❖ <b>Active Streams :</b> <code>{len(active)}</code>

<blockquote>♫ All systems are operational and running smoothly.</blockquote>"""
            )
        except Exception as e:
            await error_log("Ping Command", e)

    async def stats(client, message):
        try:
            s = await db.stats()
            await action_log("📊 Stats Command", message)

            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            ram_used = ram.used // (1024 ** 2)
            ram_total = ram.total // (1024 ** 2)

            await message.reply_text(
                f"""<blockquote><b>📊 Bot Statistics — Overview</b></blockquote>

<b>👥 Community</b>
❖ <b>Total Users :</b> <code>{s.get("users", 0)}</code>
❖ <b>Total Groups :</b> <code>{s.get("groups", 0)}</code>
❖ <b>Total Plays :</b> <code>{s.get("plays", 0)}</code>
❖ <b>Active Voice Chats :</b> <code>{len(active)}</code>

<b>🖥 System Resources</b>
❖ <b>CPU Usage :</b> <code>{cpu}%</code>
❖ <b>RAM Usage :</b> <code>{ram_used} MB / {ram_total} MB</code>
❖ <b>Session Uptime :</b> <code>{uptime()}</code>

<blockquote>🎶 Keeping the music alive across Telegram, one stream at a time.</blockquote>"""
            )
        except Exception as e:
            await error_log("Stats Command", e)

    async def cb(client, cq):
        try:
            if cq.data == "home":
                me = await client.get_me()
                bot_name = me.first_name or "{bot_name}"
                text = start_caption(cq.from_user.mention, bot_name)

                try:
                    await cq.message.edit_caption(
                        caption=text,
                        reply_markup=start_buttons(me.username),
                    )
                except Exception:
                    await cq.message.edit_text(
                        text,
                        reply_markup=start_buttons(me.username),
                    )

            elif cq.data.startswith("help"):
                page = cq.data.split(":", 1)[1]
                await cq.message.edit_text(
                    HELP.get(page, HELP["main"]),
                    reply_markup=help_buttons(page),
                )

            elif cq.data == "stats":
                s = await db.stats()
                await cq.answer(
                    f'👥 Users: {s.get("users", 0)}  |  🎵 Total Plays: {s.get("plays", 0)}  |  🔊 Active: {len(active)}',
                    show_alert=True,
                )

            else:
                await cq.answer()

        except Exception as e:
            await error_log("Callback Start/Help", e)

    app.add_handler(MessageHandler(start, filters.command("start")))
    app.add_handler(MessageHandler(ping, filters.command(["ping", "uptime", "health"])))
    app.add_handler(MessageHandler(stats, filters.command("stats")))
    app.add_handler(CallbackQueryHandler(cb, filters.regex(r"^(home|stats|help:.*)$")))