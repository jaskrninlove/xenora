# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification,
# distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

import os
import re
import random
import asyncio
import glob
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import yt_dlp


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False


# ── Paths ─────────────────────────────────────────────────────────────────────

COOKIE_DIR  = Path("cookies")
DOWNLOAD_DIR = Path("downloads")

COOKIE_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

# Player clients tried in order — each bypasses different restriction types
PLAYER_CHAINS = [
    ["android"],
    ["android", "tv_embedded"],
    ["android_vr"],
    ["tv_embedded"],
    ["web"],
]

AUDIO_EXTS = [".m4a", ".webm", ".opus", ".mp3", ".ogg"]
VIDEO_EXTS = [".mp4", ".mkv", ".webm"]


# ── Cookie & file helpers ─────────────────────────────────────────────────────

def _cookie() -> Optional[str]:
    cookies = list(COOKIE_DIR.glob("*.txt"))
    return str(random.choice(cookies)) if cookies else None


def _find_downloaded(video_id: str, video: bool) -> Optional[str]:
    """Return path of an already-downloaded file for this video_id, or None."""
    exts = VIDEO_EXTS if video else AUDIO_EXTS
    for ext in exts:
        p = DOWNLOAD_DIR / f"{video_id}{ext}"
        if p.exists() and p.stat().st_size > 10_000:   # must be >10 KB
            return str(p)
    # glob fallback — handles yt-dlp adding quality suffixes
    pattern = str(DOWNLOAD_DIR / f"{video_id}.*")
    for path in glob.glob(pattern):
        if os.path.getsize(path) > 10_000:
            return path
    return None


def _clean_old_files(keep_mb: int = 500):
    """Delete oldest downloads when folder exceeds keep_mb megabytes."""
    files = sorted(
        DOWNLOAD_DIR.glob("*.*"),
        key=lambda p: p.stat().st_mtime,
    )
    total = sum(p.stat().st_size for p in files)
    limit = keep_mb * 1024 * 1024
    for p in files:
        if total <= limit:
            break
        try:
            total -= p.stat().st_size
            p.unlink()
        except Exception:
            pass


# ── yt-dlp options builder ────────────────────────────────────────────────────

def _build_opts(
    player_clients: list,
    cookie: Optional[str],
    video: bool,
    out_tmpl: Optional[str] = None,
) -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "nocheckcertificate": True,
        "cachedir": False,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 8,
        "fragment_retries": 8,
        "skip_unavailable_fragments": True,
        "overwrites": True,
        "source_address": "0.0.0.0",
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.6422.165 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                "player_client": player_clients,
                "player_skip": ["configs"],
            }
        },
    }

    if video:
        opts["format"] = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo+bestaudio/"
            "best[height<=720]/"
            "best"
        )
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = (
            "bestaudio[ext=m4a]/"
            "bestaudio[ext=webm]/"
            "bestaudio[ext=opus]/"
            "bestaudio/"
            "best"
        )

    if cookie:
        opts["cookiefile"] = cookie

    if out_tmpl:
        opts["outtmpl"] = out_tmpl

    return opts


# ── Info extraction (no download) ─────────────────────────────────────────────

def _extract_info_only(url: str, cookie: Optional[str]) -> Optional[dict]:
    """
    Lightweight info fetch (no download). Tries every player chain.
    Returns the info dict or None.
    """
    for clients in PLAYER_CHAINS:
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "cachedir": False,
                "ignoreerrors": False,
                "socket_timeout": 20,
                "extract_flat": False,
                "extractor_args": {
                    "youtube": {
                        "player_client": clients,
                        "player_skip": ["configs"],
                    }
                },
            }
            if cookie:
                opts["cookiefile"] = cookie

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info or not isinstance(info, dict):
                continue

            # Unwrap search results
            if info.get("entries"):
                for e in info["entries"]:
                    if e and e.get("id"):
                        return e
                continue

            if info.get("id"):
                return info

        except Exception:
            continue

    return None


# ── Search: get candidate video IDs ──────────────────────────────────────────

def _search_ids(query: str, cookie: Optional[str], count: int = 5) -> list:
    """Return up to `count` YouTube video IDs matching query."""
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "cachedir": False,
            "ignoreerrors": True,
            "extract_flat": True,
            "socket_timeout": 15,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "player_skip": ["configs"],
                }
            },
        }
        if cookie:
            opts["cookiefile"] = cookie

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{count}:{query}", download=False)

        ids = []
        for e in (info or {}).get("entries") or []:
            vid_id = (e or {}).get("id")
            if vid_id and vid_id not in ids:
                ids.append(vid_id)
        return ids

    except Exception:
        return []


# ── Download a single video by ID ─────────────────────────────────────────────

def _download(video_id: str, video: bool, cookie: Optional[str]) -> Optional[str]:
    """
    Download audio/video for a given video_id.
    Tries every player chain. Returns file path or None.
    """
    # Already cached?
    cached = _find_downloaded(video_id, video)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tmpl = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    for clients in PLAYER_CHAINS:
        opts = _build_opts(clients, cookie, video, out_tmpl)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ret = ydl.download([url])

            # ret == 0 means success
            path = _find_downloaded(video_id, video)
            if path:
                return path

        except yt_dlp.utils.DownloadError as e:
            err = str(e).lower()
            # Non-retryable errors — skip remaining chains
            if any(x in err for x in ("private video", "members only", "removed")):
                return None
            continue
        except Exception:
            continue

    return None


# ── Build candidate ID list ───────────────────────────────────────────────────

def _candidate_ids(query: str, cookie: Optional[str]) -> list:
    """
    Return an ordered list of video IDs to try.
    Direct URLs are put first; search results follow.
    """
    ids: list = []
    is_url = query.startswith(("http://", "https://"))

    if is_url:
        m = YT_RE.search(query)
        if m:
            ids.append(m.group(1))

        # Also search by title in case the direct video is blocked
        info = _extract_info_only(query if not ids else f"https://www.youtube.com/watch?v={ids[0]}", cookie)
        title = (info or {}).get("title", "")
        if title:
            for vid_id in _search_ids(title, cookie, 5):
                if vid_id not in ids:
                    ids.append(vid_id)
    else:
        ids = _search_ids(query, cookie, 7)

    return ids


# ── Main extraction ───────────────────────────────────────────────────────────

def _extract(query: str, video: bool = False) -> Track:
    query = query.strip()
    cookie = _cookie()

    # Periodically clean old downloads
    _clean_old_files(keep_mb=500)

    # Build candidate list
    ids = _candidate_ids(query, cookie)

    if not ids:
        raise Exception(
            "❌ No YouTube results found.\n"
            "💡 Try a different song name or a direct YouTube link."
        )

    # Try every candidate until one downloads successfully
    for video_id in ids:
        file_path = _download(video_id, video, cookie)
        if not file_path:
            continue

        # Fetch metadata for title/thumbnail (best-effort)
        meta: dict = {}
        try:
            meta = _extract_info_only(
                f"https://www.youtube.com/watch?v={video_id}", cookie
            ) or {}
        except Exception:
            pass

        return Track(
            title=meta.get("title") or f"YouTube · {video_id}",
            url=file_path,
            webpage_url=(
                meta.get("webpage_url")
                or f"https://www.youtube.com/watch?v={video_id}"
            ),
            duration=meta.get("duration") or 0,
            thumbnail=meta.get("thumbnail") or "",
            is_video=video,
        )

    # Absolute last resort — broader search
    if not query.startswith(("http://", "https://")):
        for video_id in _search_ids(query, cookie, 15)[7:]:
            file_path = _download(video_id, video, cookie)
            if file_path:
                meta = _extract_info_only(
                    f"https://www.youtube.com/watch?v={video_id}", cookie
                ) or {}
                return Track(
                    title=meta.get("title") or f"YouTube · {video_id}",
                    url=file_path,
                    webpage_url=meta.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
                    duration=meta.get("duration") or 0,
                    thumbnail=meta.get("thumbnail") or "",
                    is_video=video,
                )

    raise Exception(
        "❌ Could not download this track after trying all available sources.\n"
        "The video may be region-locked, age-restricted, private, or removed.\n"
        "💡 Try searching by song title instead of a direct YouTube link."
    )


# ── Public async API ──────────────────────────────────────────────────────────

async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
