from dataclasses import dataclass
import asyncio
import yt_dlp


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False


BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "geo_bypass": True,
    "cachedir": False,
    "socket_timeout": 15,
    "extract_flat": False,
    "ignoreerrors": True,
    "source_address": "0.0.0.0",
    "cookiefile": "cookies/cookies.txt",
}


def _make_opts(video: bool = False, fallback: bool = False):
    opts = BASE_OPTS.copy()

    if fallback:
        opts["format"] = "best/bestaudio/bestvideo"
    elif video:
        opts["format"] = (
            "best[height<=720]/"
            "bestvideo[height<=720]+bestaudio/"
            "best"
        )
    else:
        opts["format"] = (
            "bestaudio[ext=m4a]/"
            "bestaudio[ext=webm]/"
            "bestaudio/best"
        )

    return opts


def _pick_info(info):
    if not isinstance(info, dict):
        return None

    entries = info.get("entries")
    if entries:
        for entry in entries:
            if entry and isinstance(entry, dict):
                if entry.get("url") or entry.get("formats"):
                    return entry
        for entry in entries:
            if entry and isinstance(entry, dict):
                return entry
        return None

    return info


def _get_best_format_url(info, video: bool = False):
    if not isinstance(info, dict):
        return ""

    if info.get("url"):
        return info["url"]

    formats = info.get("formats") or []
    if not formats:
        return ""

    if video:
        for fmt in reversed(formats):
            url = fmt.get("url")
            vcodec = fmt.get("vcodec")
            acodec = fmt.get("acodec")
            height = fmt.get("height") or 0

            if url and vcodec != "none" and acodec != "none" and height <= 720:
                return url

        for fmt in reversed(formats):
            url = fmt.get("url")
            vcodec = fmt.get("vcodec")
            height = fmt.get("height") or 0

            if url and vcodec != "none" and height <= 720:
                return url

    for fmt in reversed(formats):
        url = fmt.get("url")
        acodec = fmt.get("acodec")

        if url and acodec != "none":
            return url

    for fmt in reversed(formats):
        if fmt.get("url"):
            return fmt["url"]

    return ""


def _extract_once(search: str, video: bool = False, fallback: bool = False):
    with yt_dlp.YoutubeDL(_make_opts(video, fallback)) as ydl:
        info = ydl.extract_info(search, download=False)

    info = _pick_info(info)
    if not info:
        return None

    url = _get_best_format_url(info, video)

    if not url:
        return None

    return Track(
        title=info.get("title", "Unknown Track"),
        url=url,
        webpage_url=info.get("webpage_url") or info.get("original_url") or "",
        duration=info.get("duration") or 0,
        thumbnail=info.get("thumbnail") or "",
        is_video=video,
    )


def _extract(query: str, video: bool = False) -> Track:
    query = query.strip()

    searches = []

    if query.startswith(("http://", "https://")):
        searches.append(query)
    else:
        searches.append(f"ytsearch1:{query}")
        searches.append(f"ytsearch3:{query}")

    for search in searches:
        try:
            track = _extract_once(search, video=video, fallback=False)
            if track:
                return track
        except Exception:
            pass

        try:
            track = _extract_once(search, video=video, fallback=True)
            if track:
                return track
        except Exception:
            pass

    raise Exception(
        "This video is available on YouTube, but no playable stream was returned. "
        "Try another upload, shorter title, or add YouTube cookies."
    )


async def get_track(query: str, video: bool = False) -> Track:
    return await asyncio.to_thread(_extract, query, video)
