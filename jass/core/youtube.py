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
    exts = [".mp4", ".mkv", ".webm"] if video else [".m4a", ".webm", ".opus", ".mp3"]
    for ext in exts:
        path = DOWNLOAD_DIR / f"{video_id}{ext}"
        if path.exists() and path.stat().st_size > 0:
            return str(path)
    return None


def base_opts(cookie=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cachedir": False,
        "overwrites": False,
        "ignoreerrors": True,
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "source_address": "0.0.0.0",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    if cookie:
        opts["cookiefile"] = cookie

    return opts


def search_info(query: str):
    cookie = get_cookie()
    searches = []

    if query.startswith(("http://", "https://")):
        searches.append(query)
    else:
        searches.extend([
            f"ytsearch1:{query}",
            f"ytsearch3:{query}",
            f"ytsearch5:{query}",
        ])

    for search in searches:
        try:
            opts = base_opts(cookie)
            opts["default_search"] = "ytsearch"
            opts["extract_flat"] = False
            opts["format"] = "bestaudio/best"

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


def download_by_id(video_id: str, video: bool):
    cached = find_file(video_id, video)
    if cached:
        return cached

    cookie = get_cookie()
    url = f"https://www.youtube.com/watch?v={video_id}"

    opts = base_opts(cookie)
    opts["outtmpl"] = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    if video:
        opts.update({
            "format": "bv*[height<=720]+ba/bv*+ba/b",
            "merge_output_format": "mp4",
        })
    else:
        opts.update({
            "format": "ba/bestaudio/best",
        })

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    return find_file(video_id, video)


def _extract(query: str, video: bool = False) -> Track:
    query = query.strip()

    direct_id = get_video_id(query)
    info = None

    if direct_id:
        info = {"id": direct_id, "webpage_url": f"https://www.youtube.com/watch?v={direct_id}"}
    else:
        info = search_info(query)

    if not info:
        raise Exception("No YouTube result found. Try a different title or direct link.")

    video_id = info.get("id")
    if not video_id:
        raise Exception("Could not read YouTube video ID.")

    file_path = download_by_id(video_id, video)

    if not file_path or not os.path.exists(file_path):
        raise Exception(
            "This YouTube video could not be downloaded. It may be private, region-blocked, age-restricted, or protected."
        )

    title = info.get("title") or f"YouTube Video {video_id}"
    webpage_url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"

    return Track(
        title=title,
        url=file_path,
        webpage_url=webpage_url,
        duration=info.get("duration") or 0,
        thumbnail=info.get("thumbnail") or "",
        is_video=video,
    )


async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
