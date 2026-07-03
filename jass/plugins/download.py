# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

import os
import asyncio
import tempfile
import yt_dlp

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from ..core.logger import action_log, error_log
from ..helpers.premium import render
from pyrogram.enums import ParseMode

def temp_path(prefix: str):
    return os.path.join(tempfile.gettempdir(), f"{prefix}_%(id)s.%(ext)s")


_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": temp_path("jass_song"),
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "geo_bypass": True,
    "ignoreerrors": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

_VIDEO_OPTS = {
    "format": "best[height<=720][ext=mp4]/best[ext=mp4]/best",
    "outtmpl": temp_path("jass_video"),
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "geo_bypass": True,
    "ignoreerrors": True,
}


async def run_blocking(func):
    return await asyncio.to_thread(func)


async def download_media(query: str, opts: dict):
    def runner():
        search = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search, download=True)

            if "entries" in info:
                info = next((x for x in info["entries"] if x), None)

            if not info:
                raise Exception("No result found.")

            file_path = ydl.prepare_filename(info)

            if opts is _AUDIO_OPTS:
                base = os.path.splitext(file_path)[0]
                for ext in [".mp3", ".m4a", ".opus", ".ogg", ".webm"]:
                    if os.path.exists(base + ext):
                        file_path = base + ext
                        break

            duration = int(info.get("duration") or 0)

            return {
                "title": info.get("title", "Unknown"),
                "file": file_path,
                "duration": f"{duration // 60}:{duration % 60:02d}",
                "duration_sec": duration,
                "thumbnail": info.get("thumbnail", ""),
                "uploader": info.get("uploader", "Unknown"),
            }

    return await run_blocking(runner)


async def fetch_thumbnail(query: str):
    def runner():
        search = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(
            {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "default_search": "ytsearch1",
                "geo_bypass": True,
                "ignoreerrors": True,
            }
        ) as ydl:
            info = ydl.extract_info(search, download=False)

            if "entries" in info:
                info = next((x for x in info["entries"] if x), None)

            if not info:
                raise Exception("No result found.")

            duration = int(info.get("duration") or 0)

            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": f"{duration // 60}:{duration % 60:02d}",
                "uploader": info.get("uploader", "Unknown"),
            }

    return await run_blocking(runner)


def safe_remove(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


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

    async def song(client, message):
        if len(message.command) < 2:
            return await premium_reply(
                message,
                ":download: <b>Song Download Usage</b>\n\n"
                "<blockquote>"
                ":music: <b>/song</b> <code>[song name or URL]</code>\n"
                ":success: Downloads and sends the audio file.\n\n"
                "Supports YouTube, SoundCloud and more."
                "</blockquote>",
            )

        query = " ".join(message.command[1:])
        status = await premium_reply(
            message,
            f":download: <b>Downloading Audio</b>\n\n"
            f"<blockquote>"
            f":search: <b>Query:</b> <code>{query}</code>\n"
            f":settings: <b>Status:</b> <i>Fetching track...</i>"
            f"</blockquote>",
        )

        file = None

        try:
            await action_log("Song Download", message)
            info = await download_media(query, _AUDIO_OPTS)
            file = info["file"]

            await status.delete()
            me = await client.get_me()
            bot_name = me.first_name

            await message.reply_audio(
                audio=file,
                title=info["title"],
                performer=info["uploader"],
                duration=info["duration_sec"],
                caption=render(
                    f":music: <b>{info['title']}</b>\n\n"
                    f"<blockquote>"
                    f":time: <b>Duration:</b> <code>{info['duration']}</code>\n"
                    f":profile: <b>Artist:</b> {info['uploader']}\n\n"
                    f"Downloaded via {bot_name}"
                    f"</blockquote>"
                ),
                parse_mode=ParseMode.HTML,
            )

        except Exception as e:
            await error_log("Song Download", e)
            await premium_edit(
                status,
                f":error: <b>Download Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

        finally:
            safe_remove(file)

    async def video(client, message):
        if len(message.command) < 2:
            return await premium_reply(
                message,
                ":video: <b>Video Download Usage</b>\n\n"
                "<blockquote>"
                ":video: <b>/video</b> <code>[video name or URL]</code>\n"
                ":success: Downloads and sends a video file.\n\n"
                "Capped at 720p for Telegram limits."
                "</blockquote>",
            )

        query = " ".join(message.command[1:])
        status = await premium_reply(
            message,
            f":video: <b>Downloading Video</b>\n\n"
            f"<blockquote>"
            f":search: <b>Query:</b> <code>{query}</code>\n"
            f":settings: <b>Status:</b> <i>Fetching video...</i>"
            f"</blockquote>",
        )

        file = None

        try:
            await action_log("Video Download", message)
            info = await download_media(query, _VIDEO_OPTS)
            file = info["file"]

            if not os.path.exists(file):
                raise Exception("Downloaded file not found.")

            if os.path.getsize(file) > 2_000_000_000:
                await premium_edit(
                    status,
                    ":error: <b>File Too Large</b>\n\n"
                    "<blockquote>The video exceeds Telegram's 2 GB file size limit.</blockquote>",
                )
                return

            await status.delete()
            me = await client.get_me()
            bot_name = me.first_name

            await message.reply_video(
                video=file,
                caption=render(
                    f":video: <b>{info['title']}</b>\n\n"
                    f"<blockquote>"
                    f":time: <b>Duration:</b> <code>{info['duration']}</code>\n"
                    f":profile: <b>Channel:</b> {info['uploader']}\n\n"
                    f"Downloaded via {bot_name}"
                    f"</blockquote>"
                ),
                parse_mode=ParseMode.HTML,
            )

        except Exception as e:
            await error_log("Video Download", e)
            await premium_edit(
                status,
                f":error: <b>Download Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

        finally:
            safe_remove(file)

    async def thumbnail(client, message):
        if len(message.command) < 2:
            return await premium_reply(
                message,
                ":thumb: <b>Thumbnail Usage</b>\n\n"
                "<blockquote>"
                ":thumb: <b>/thumbnail</b> <code>[YouTube URL or name]</code>\n"
                ":success: Fetches the video thumbnail."
                "</blockquote>",
            )

        query = " ".join(message.command[1:])
        status = await premium_reply(
            message,
            f":thumb: <b>Fetching Thumbnail</b>\n\n"
            f"<blockquote>:search: <b>Query:</b> <code>{query}</code></blockquote>",
        )

        try:
            await action_log("Thumbnail", message)
            info = await fetch_thumbnail(query)

            if not info["thumbnail"]:
                return await premium_edit(
                    status,
                    ":warning: <b>No Thumbnail Found</b>\n\n"
                    "<blockquote>No thumbnail was found for this query.</blockquote>",
                )

            await status.delete()
            me = await client.get_me()
            bot_name = me.first_name

            await message.reply_photo(
                photo=info["thumbnail"],
                caption=render(
                    f":thumb: <b>{info['title']}</b>\n\n"
                    f"<blockquote>"
                    f":time: <b>Duration:</b> <code>{info['duration']}</code>\n"
                    f":profile: <b>Channel:</b> {info['uploader']}\n\n"
                    f"Fetched via {bot_name}"
                    f"</blockquote>"
                ),
                parse_mode=ParseMode.HTML,
            )

        except Exception as e:
            await error_log("Thumbnail Command", e)
            await premium_edit(
                status,
                f":error: <b>Thumbnail Failed</b>\n\n"
                f"<blockquote>:warning: <b>Error:</b> <code>{e}</code></blockquote>",
            )

    app.add_handler(MessageHandler(song, filters.command("song")))
    app.add_handler(MessageHandler(video, filters.command("video")))
    app.add_handler(MessageHandler(thumbnail, filters.command(["thumbnail", "thumb"])))