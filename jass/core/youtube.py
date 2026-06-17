# ==========================================================
# JassMusic
# Copyright (c) 2026 Jass
# Proprietary Software. Unauthorized copying, modification,
# distribution, or resale of this source code is strictly prohibited.
# Developed by Jass (Jaskaran Singh)
# © 2026 All Rights Reserved.
# ==========================================================

"""
YouTube extractor for JassMusic.

HOW IT WORKS (3 layers):
  Layer 1 — yt-dlp with cookie file (bypasses bot check when logged-in cookies present)
  Layer 2 — yt-dlp-invidious plugin (auto-fallback when YouTube says "not a robot")
  Layer 3 — Search for alternative candidates and retry layers 1+2 on each

SETUP (required for Layer 1):
  1. Install the cookies browser extension:
     https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
  2. Log in to YouTube in your browser.
  3. Export cookies as Netscape format → save as  cookies/youtube.txt
  4. Refresh cookies every 2–4 weeks.

SETUP (required for Layer 2 — Invidious fallback):
  pip install yt-dlp-invidious
  (already in requirements.txt)
"""

import os
import re
import glob
import random
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import yt_dlp


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False


# ── Paths ─────────────────────────────────────────────────────────────────────

COOKIE_DIR   = Path("cookies")
DOWNLOAD_DIR = Path("downloads")

COOKIE_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

AUDIO_EXTS = [".m4a", ".webm", ".opus", ".mp3", ".ogg"]
VIDEO_EXTS = [".mp4", ".mkv", ".webm"]

# Max folder size before old files get pruned
MAX_CACHE_MB = 800


# ── Cookie helpers ────────────────────────────────────────────────────────────

def _cookie() -> Optional[str]:
    """Return a random cookie file from the cookies/ dir, or None."""
    files = list(COOKIE_DIR.glob("*.txt"))
    return str(random.choice(files)) if files else None


def _has_cookies() -> bool:
    return bool(list(COOKIE_DIR.glob("*.txt")))


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _find_cached(video_id: str, video: bool) -> Optional[str]:
    """Return path of a valid cached file for this video_id, or None."""
    exts = VIDEO_EXTS if video else AUDIO_EXTS
    for ext in exts:
        p = DOWNLOAD_DIR / f"{video_id}{ext}"
        if p.exists() and p.stat().st_size > 10_000:
            return str(p)
    # yt-dlp sometimes appends quality info — glob catches those
    for path in glob.glob(str(DOWNLOAD_DIR / f"{video_id}.*")):
        if os.path.getsize(path) > 10_000:
            return path
    return None


def _prune_cache():
    """Delete oldest files when the downloads folder exceeds MAX_CACHE_MB."""
    files = sorted(DOWNLOAD_DIR.glob("*.*"), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in files)
    limit = MAX_CACHE_MB * 1024 * 1024
    for p in files:
        if total <= limit:
            break
        try:
            total -= p.stat().st_size
            p.unlink()
        except Exception:
            pass


# ── yt-dlp options ────────────────────────────────────────────────────────────

def _base_opts(video: bool, cookie: Optional[str], use_invidious: bool = False) -> dict:
    """
    Build yt-dlp options.
    use_invidious=True forces the Invidious extractor (Layer 2).
    """
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
        "retries": 5,
        "fragment_retries": 5,
        "skip_unavailable_fragments": True,
        "overwrites": True,
        "source_address": "0.0.0.0",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    if use_invidious:
        # Force Invidious extractor — bypasses YouTube bot check entirely
        opts["allowed_extractors"] = ["Invidious", "InvidiousPlaylist", "default", "-youtube", "-youtubeplaylist"]
        opts["extractor_args"] = {
            "invidious": {
                "max_retries": "3",
                "retry_interval": "2",
            }
        }
    else:
        opts["extractor_args"] = {
            "youtube": {
                # android client bypasses most geo/age restrictions
                "player_client": ["android", "tv_embedded", "web"],
                "player_skip": ["configs"],
            }
        }

    if video:
        opts["format"] = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=480]+bestaudio/"
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

    if cookie and not use_invidious:
        opts["cookiefile"] = cookie

    return opts


# ── Search ────────────────────────────────────────────────────────────────────

def _search_video_ids(query: str, count: int = 7) -> list:
    """Return up to `count` YouTube video IDs for a text query."""
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
        cookie = _cookie()
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


# ── Download (with bot-detection fallback to Invidious) ───────────────────────

def _download_one(video_id: str, video: bool) -> Optional[str]:
    """
    Download a single video/audio by ID.

    Strategy:
      1. Return cached file if available.
      2. Try with cookies (Layer 1) — works when youtube.txt is present.
      3. If bot-detected or failed → retry via Invidious (Layer 2).
    """
    cached = _find_cached(video_id, video)
    if cached:
        return cached

    url = f"https://www.youtube.com/watch?v={video_id}"
    cookie = _cookie()

    # ── Layer 1: standard yt-dlp + cookies ────────────────────────────────
    bot_detected = False
    try:
        opts = _base_opts(video, cookie, use_invidious=False)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        path = _find_cached(video_id, video)
        if path:
            return path
    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if "sign in" in err or "not a bot" in err or "confirm" in err:
            bot_detected = True
        elif any(x in err for x in ("private video", "members only", "has been removed")):
            return None  # Unrecoverable — skip
    except Exception:
        bot_detected = True  # Treat unknown errors as potentially recoverable

    # ── Layer 2: Invidious fallback ────────────────────────────────────────
    # Triggered when: no cookies, bot detected, or Layer 1 failed
    if bot_detected or not _has_cookies():
        try:
            # yt-dlp-invidious plugin must be installed:
            # pip install yt-dlp-invidious
            opts = _base_opts(video, None, use_invidious=True)
            # Invidious uses video ID directly
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_id])
            path = _find_cached(video_id, video)
            if path:
                return path
        except Exception:
            pass

    return None


# ── Metadata fetch ─────────────────────────────────────────────────────────────

def _fetch_meta(video_id: str) -> dict:
    """Fetch title/duration/thumbnail without downloading. Best-effort."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cookie = _cookie()
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "nocheckcertificate": True,
            "cachedir": False,
            "ignoreerrors": True,
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
            info = ydl.extract_info(url, download=False)
        return info or {}
    except Exception:
        return {}


# ── Candidate builder ─────────────────────────────────────────────────────────

def _build_candidates(query: str) -> list:
    """
    Return ordered list of video IDs to try.
    Direct URL → put that ID first, then search by title.
    Text query → search directly.
    """
    ids: list = []
    is_url = query.startswith(("http://", "https://"))

    if is_url:
        m = YT_RE.search(query)
        if m:
            ids.append(m.group(1))
        # Also search by title in case the direct video is blocked
        if ids:
            meta = _fetch_meta(ids[0])
            title = meta.get("title", "")
            if title:
                for vid_id in _search_video_ids(title, 5):
                    if vid_id not in ids:
                        ids.append(vid_id)
        else:
            # Non-YouTube URL or unrecognised — try searching the raw text
            for vid_id in _search_video_ids(query, 5):
                if vid_id not in ids:
                    ids.append(vid_id)
    else:
        ids = _search_video_ids(query, 7)

    return ids


# ── Main extraction ───────────────────────────────────────────────────────────

def _extract(query: str, video: bool = False) -> Track:
    query = query.strip()
    _prune_cache()

    candidates = _build_candidates(query)

    if not candidates:
        raise Exception(
            "❌ No YouTube results found.\n"
            "💡 Try a different song name or a direct YouTube link."
        )

    for video_id in candidates:
        file_path = _download_one(video_id, video)
        if not file_path:
            continue

        meta = _fetch_meta(video_id)
        return Track(
            title=meta.get("title") or f"Track · {video_id}",
            url=file_path,
            webpage_url=meta.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
            duration=meta.get("duration") or 0,
            thumbnail=meta.get("thumbnail") or "",
            is_video=video,
        )

    raise Exception(
        "❌ Could not download this track after trying all sources.\n"
        "Possible reasons: region-locked, age-restricted, private, or removed.\n\n"
        "✅ Fix: Add a YouTube cookie file to the cookies/ folder.\n"
        "   → Export from Chrome/Firefox using the 'Get cookies.txt' extension\n"
        "   → Save as  cookies/youtube.txt\n"
        "   → Refresh every 2–4 weeks"
    )


# ── Public async API ──────────────────────────────────────────────────────────

async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
