import os
import re
import random
import asyncio
from pathlib import Path
from dataclasses import dataclass

import yt_dlp
from py_yt import VideosSearch


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False


COOKIE_DIR = Path("cookies")
DOWNLOAD_DIR = Path("downloads")

COOKIE_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

YT_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})")


def get_cookies():
    return [str(x) for x in COOKIE_DIR.glob("*.txt")]


def get_video_id(text: str):
    match = YT_ID_RE.search(text or "")
    return match.group(1) if match else None


def to_seconds(duration: str):
    if not duration:
        return 0
    try:
        parts = [int(x) for x in str(duration).split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]
    except Exception:
        return 0


def find_file(video_id: str, video: bool):
    exts = [".mp4", ".webm", ".mkv"] if video else [".webm", ".m4a", ".opus", ".mp3"]
    for ext in exts:
        path = DOWNLOAD_DIR / f"{video_id}{ext}"
        if path.exists() and path.stat().st_size > 0:
            return str(path)
    return None


def search_youtube(query: str):
    video_id = get_video_id(query)

    if video_id:
        return {
            "id": video_id,
            "title": f"YouTube Video {video_id}",
            "link": f"https://www.youtube.com/watch?v={video_id}",
            "duration": None,
            "thumbnail": "",
        }

    try:
        search = VideosSearch(query, limit=5, with_live=False)
        results = asyncio.run(search.next())

        for item in results.get("result", []):
            vid = item.get("id")
            if not vid:
                continue

            thumbnails = item.get("thumbnails") or []
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""

            return {
                "id": vid,
                "title": item.get("title") or f"YouTube Video {vid}",
                "link": item.get("link") or f"https://www.youtube.com/watch?v={vid}",
                "duration": item.get("duration"),
                "thumbnail": thumbnail.split("?")[0] if thumbnail else "",
            }

    except Exception as e:
        print("YouTube search failed:", e)

    return None


def ydl_base_opts(cookiefile=None):
    opts = {
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cachedir": False,
        "overwrites": False,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,

        # IMPORTANT: avoid youtube+invidious route
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["dash", "hls"],
            }
        },
    }

    if cookiefile:
        opts["cookiefile"] = cookiefile

    return opts


def download(video_id: str, video: bool = False):
    cached = find_file(video_id, video)
    if cached:
        return cached

    url = f"youtube:{video_id}"

    cookies = get_cookies()
    if not cookies:
        cookies = [None]
    else:
        random.shuffle(cookies)

    formats = (
        ["best[ext=mp4]/best", "best"]
        if video
        else ["bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best", "best"]
    )

    last_error = None

    for cookie in cookies:
        for fmt in formats:
            try:
                opts = ydl_base_opts(cookie)
                opts["format"] = fmt

                if video:
                    opts["merge_output_format"] = "mp4"

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                cached = find_file(video_id, video)
                if cached:
                    return cached

            except Exception as e:
                last_error = e
                continue

    raise Exception(f"YouTube download failed: {last_error}")


def _extract(query: str, video: bool = False) -> Track:
    data = search_youtube(query)

    if not data:
        raise Exception("No YouTube result found. Try another title or direct YouTube link.")

    video_id = data["id"]
    file_path = download(video_id, video)

    if not file_path or not os.path.exists(file_path):
        raise Exception("Download failed. Try another upload or refresh cookies.")

    return Track(
        title=data.get("title") or f"YouTube Video {video_id}",
        url=file_path,
        webpage_url=data.get("link") or f"https://www.youtube.com/watch?v={video_id}",
        duration=to_seconds(data.get("duration")),
        thumbnail=data.get("thumbnail") or "",
        is_video=video,
    )


async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
