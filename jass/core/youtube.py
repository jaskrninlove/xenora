import os
import re
import random
import asyncio
from pathlib import Path
from dataclasses import dataclass

import yt_dlp


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

YT_RE = re.compile(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})")


def get_cookie():
    cookies = list(COOKIE_DIR.glob("*.txt"))
    return str(random.choice(cookies)) if cookies else None


def get_video_id(query: str):
    match = YT_RE.search(query)
    return match.group(1) if match else None


def find_file(video_id: str, video: bool):
    exts = [".mp4", ".webm", ".mkv"] if video else [".webm", ".m4a", ".opus", ".mp3"]
    for ext in exts:
        path = DOWNLOAD_DIR / f"{video_id}{ext}"
        if path.exists() and path.stat().st_size > 0:
            return str(path)
    return None


def base_opts():
    cookie = get_cookie()

    opts = {
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
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
    }

    if cookie:
        opts["cookiefile"] = cookie

    return opts


def search_info(query: str):
    query = query.strip()

    searches = [query] if query.startswith(("http://", "https://")) else [
        f"ytsearch1:{query}",
        f"ytsearch3:{query}",
        f"ytsearch5:{query}",
    ]

    for search in searches:
        try:
            opts = base_opts()
            opts["default_search"] = "ytsearch"
            opts["extract_flat"] = False
            opts["format"] = "best"

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search, download=False)

            if isinstance(info, dict) and info.get("entries"):
                for entry in info["entries"]:
                    if entry and entry.get("id"):
                        return entry

            if isinstance(info, dict) and info.get("id"):
                return info

        except Exception:
            continue

    return None


def download_video(video_id: str):
    cached = find_file(video_id, True)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"

    formats = [
        "18",                 # mp4 360p with audio - most stable
        "22",                 # mp4 720p with audio if available
        "136+140",            # mp4 720p video + m4a audio
        "134+140",            # mp4 360p video + m4a audio
        "best[ext=mp4]/best",
        "best",
    ]

    for fmt in formats:
        try:
            opts = base_opts()
            opts["format"] = fmt
            opts["merge_output_format"] = "mp4"

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)

            cached = find_file(video_id, True)
            if cached:
                return cached

        except Exception:
            continue

    return None


def download_audio(video_id: str):
    cached = find_file(video_id, False)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"

    formats = [
        "140",                # m4a medium
        "251",                # webm opus
        "249",                # webm opus low
        "bestaudio/best",
        "best",
    ]

    for fmt in formats:
        try:
            opts = base_opts()
            opts["format"] = fmt

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)

            cached = find_file(video_id, False)
            if cached:
                return cached

        except Exception:
            continue

    return None


def _extract(query: str, video: bool = False) -> Track:
    query = query.strip()

    direct_id = get_video_id(query)
    info = None

    if direct_id:
        info = {
            "id": direct_id,
            "title": f"YouTube Video {direct_id}",
            "webpage_url": f"https://www.youtube.com/watch?v={direct_id}",
            "duration": 0,
            "thumbnail": "",
        }
    else:
        info = search_info(query)

    if not info:
        raise Exception("No YouTube result found. Try another title or direct link.")

    video_id = info.get("id")
    if not video_id:
        raise Exception("Could not read YouTube video ID.")

    file_path = download_video(video_id) if video else download_audio(video_id)

    if not file_path or not os.path.exists(file_path):
        raise Exception(
            "This video could not be played. It may be region-blocked, private, age-restricted, or protected by YouTube."
        )

    return Track(
        title=info.get("title", f"YouTube Video {video_id}"),
        url=file_path,
        webpage_url=info.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
        duration=info.get("duration") or 0,
        thumbnail=info.get("thumbnail") or "",
        is_video=video,
    )


async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
