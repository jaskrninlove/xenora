from dataclasses import dataclass
import asyncio
import re
from urllib.parse import quote_plus

import aiohttp

from ..config import config


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False


SPOTIFY_TRACK_RE = re.compile(r"(?:spotify\.com/track/|spotify:track:)([A-Za-z0-9]+)")


def _duration(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def _best_image(images):
    if not images:
        return ""
    if isinstance(images, list):
        last = images[-1]
        if isinstance(last, dict):
            return last.get("url", "")
        return str(last)
    return ""


def _best_download(downloads):
    if not downloads:
        return ""

    if isinstance(downloads, list):
        for q in ("320kbps", "320", "160kbps", "160", "96kbps", "96"):
            for item in downloads:
                if not isinstance(item, dict):
                    continue
                quality = str(item.get("quality", "")).lower()
                url = item.get("url", "")
                if q.lower() in quality and url:
                    return url

        for item in reversed(downloads):
            if isinstance(item, dict) and item.get("url"):
                return item["url"]

    if isinstance(downloads, str):
        return downloads

    return ""


async def _spotify_token(session):
    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        return None

    async with session.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=aiohttp.BasicAuth(
            config.SPOTIFY_CLIENT_ID,
            config.SPOTIFY_CLIENT_SECRET,
        ),
        timeout=20,
    ) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
        return data.get("access_token")


async def _spotify_to_query(query: str):
    match = SPOTIFY_TRACK_RE.search(query)
    if not match:
        return query

    track_id = match.group(1)

    async with aiohttp.ClientSession() as session:
        token = await _spotify_token(session)
        if not token:
            return query

        async with session.get(
            f"https://api.spotify.com/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        ) as resp:
            if resp.status != 200:
                return query

            data = await resp.json()
            name = data.get("name", "")
            artists = ", ".join(a.get("name", "") for a in data.get("artists", []))
            return f"{name} {artists}".strip() or query


async def _saavn_search(query: str):
    base = config.SAAVN_API_URL.rstrip("/")
    url = f"{base}/search/songs?query={quote_plus(query)}&limit=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as resp:
            if resp.status != 200:
                raise Exception("JioSaavn API search failed.")
            data = await resp.json()

        results = (
            data.get("data", {}).get("results")
            or data.get("results")
            or []
        )

        if not results:
            raise Exception("No song found on JioSaavn.")

        song = results[0]
        song_id = song.get("id")

        if song_id and not song.get("downloadUrl"):
            detail_url = f"{base}/songs?id={song_id}"
            async with session.get(detail_url, timeout=30) as resp:
                if resp.status == 200:
                    detail = await resp.json()
                    detail_data = detail.get("data")
                    if isinstance(detail_data, list) and detail_data:
                        song = detail_data[0]
                    elif isinstance(detail_data, dict):
                        song = detail_data

        audio_url = _best_download(song.get("downloadUrl") or song.get("download_url"))

        if not audio_url:
            raise Exception("Song found, but no playable audio URL returned.")

        title = song.get("name") or song.get("title") or "Unknown Track"
        artists = song.get("primaryArtists") or song.get("primary_artists") or ""
        if isinstance(artists, list):
            artists = ", ".join(a.get("name", "") for a in artists if isinstance(a, dict))

        full_title = f"{title} - {artists}".strip(" -")

        return Track(
            title=full_title,
            url=audio_url,
            webpage_url=song.get("url") or "",
            duration=_duration(song.get("duration")),
            thumbnail=_best_image(song.get("image")),
            is_video=False,
        )


async def get_track(query: str, video: bool = False) -> Track:
    query = await _spotify_to_query(query)
    return await _saavn_search(query)
