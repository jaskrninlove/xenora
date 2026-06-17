import os
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


def get_cookie():
    cookies = list(COOKIE_DIR.glob("*.txt"))
    if not cookies:
        return None
    return str(random.choice(cookies))


def ydl_opts(video: bool = False):
    cookie = get_cookie()

    base = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cachedir": False,
        "overwrites": False,
        "ignoreerrors": False,
        "socket_timeout": 20,
    }

    if cookie:
        base["cookiefile"] = cookie

    if video:
        base.update(
            {
                "format": "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]/best",
                "merge_output_format": "mp4",
            }
        )
    else:
        base.update(
            {
                "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
            }
        )

    return base


def search_opts():
    cookie = get_cookie()

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch1",
        "geo_bypass": True,
        "extract_flat": False,
        "cachedir": False,
        "socket_timeout": 15,
    }

    if cookie:
        opts["cookiefile"] = cookie

    return opts


def find_file(video_id: str, video: bool = False):
    exts = [".mp4", ".mkv", ".webm"] if video else [".m4a", ".webm", ".opus", ".mp3"]
    for ext in exts:
        path = DOWNLOAD_DIR / f"{video_id}{ext}"
        if path.exists():
            return str(path)
    return None


def _search_info(query: str):
    search = query.strip()

    if not search.startswith(("http://", "https://")):
        search = f"ytsearch1:{search}"

    with yt_dlp.YoutubeDL(search_opts()) as ydl:
        info = ydl.extract_info(search, download=False)

    if isinstance(info, dict) and info.get("entries"):
        for entry in info["entries"]:
            if entry:
                return entry

    return info if isinstance(info, dict) else None


def _download(video_id: str, video: bool = False):
    cached = find_file(video_id, video)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"

    with yt_dlp.YoutubeDL(ydl_opts(video)) as ydl:
        ydl.download([url])

    return find_file(video_id, video)


def _extract(query: str, video: bool = False) -> Track:
    info = _search_info(query)

    if not info:
        raise Exception("No YouTube result found. Try another song name.")

    video_id = info.get("id")
    if not video_id:
        raise Exception("Could not get YouTube video ID.")

    file_path = _download(video_id, video)

    if not file_path or not os.path.exists(file_path):
        raise Exception("Download failed. Try another upload or refresh cookies.")

    return Track(
        title=info.get("title", "Unknown Track"),
        url=file_path,
        webpage_url=info.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
        duration=info.get("duration") or 0,
        thumbnail=info.get("thumbnail") or "",
        is_video=video,
    )


async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
