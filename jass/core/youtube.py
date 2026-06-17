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


def get_cookie():
    cookies = list(COOKIE_DIR.glob("*.txt"))
    return str(random.choice(cookies)) if cookies else None


def get_video_id(text: str):
    m = YT_ID_RE.search(text or "")
    return m.group(1) if m else None


def to_seconds(duration):
    if not duration:
        return 0
    try:
        p = [int(x) for x in str(duration).split(":")]
        if len(p) == 3:
            return p[0] * 3600 + p[1] * 60 + p[2]
        if len(p) == 2:
            return p[0] * 60 + p[1]
        return p[0]
    except Exception:
        return 0


def find_file(video_id: str, video: bool):
    exts = [".mp4", ".webm", ".mkv"] if video else [".webm", ".m4a", ".mp3", ".opus"]
    for ext in exts:
        p = DOWNLOAD_DIR / f"{video_id}{ext}"
        if p.exists() and p.stat().st_size > 0:
            return str(p)
    return None


def search_youtube(query: str):
    vid = get_video_id(query)
    if vid:
        return {
            "id": vid,
            "title": f"YouTube Video {vid}",
            "link": f"https://www.youtube.com/watch?v={vid}",
            "duration": None,
            "thumbnail": "",
        }

    try:
        s = VideosSearch(query, limit=5, with_live=False)
        r = asyncio.run(s.next())

        for item in r.get("result", []):
            vid = item.get("id")
            if not vid:
                continue

            thumbs = item.get("thumbnails") or []
            thumb = thumbs[-1].get("url", "") if thumbs else ""

            return {
                "id": vid,
                "title": item.get("title") or f"YouTube Video {vid}",
                "link": item.get("link") or f"https://www.youtube.com/watch?v={vid}",
                "duration": item.get("duration"),
                "thumbnail": thumb.split("?")[0] if thumb else "",
            }
    except Exception as e:
        print("YouTube search failed:", e)

    return None


def ydl_opts(video: bool, cookie=None):
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
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,
        "socket_timeout": 30,
        "format": "best" if video else "bestaudio/best",
    }

    if video:
        opts["merge_output_format"] = "mp4"

    if cookie:
        opts["cookiefile"] = cookie

    return opts


def download(video_id: str, video: bool):
    cached = find_file(video_id, video)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"

    cookies = list(COOKIE_DIR.glob("*.txt"))
    random.shuffle(cookies)
    cookie_list = [str(c) for c in cookies] or [None]

    last_error = None

    for cookie in cookie_list:
        try:
            with yt_dlp.YoutubeDL(ydl_opts(video, cookie)) as ydl:
                ydl.download([url])

            cached = find_file(video_id, video)
            if cached:
                return cached

        except Exception as e:
            last_error = e
            continue

    raise Exception(f"YouTube download failed: {last_error}")


def _extract(query: str, video: bool = False):
    data = search_youtube(query)

    if not data:
        raise Exception("No YouTube result found. Try direct YouTube link.")

    video_id = data["id"]
    file_path = download(video_id, video)

    if not file_path or not os.path.exists(file_path):
        raise Exception("Download failed.")

    return Track(
        title=data.get("title") or f"YouTube Video {video_id}",
        url=file_path,
        webpage_url=data.get("link") or f"https://www.youtube.com/watch?v={video_id}",
        duration=to_seconds(data.get("duration")),
        thumbnail=data.get("thumbnail") or "",
        is_video=video,
    )


async def get_track(query: str, video: bool = False):
    return await asyncio.to_thread(_extract, query, video)
