from dataclasses import dataclass
import asyncio
from urllib.parse import quote_plus
import aiohttp
import yt_dlp

from ..config import config


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_video: bool = False
    source: str = "Music"


def _duration(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def _best_image(images):
    if isinstance(images, list) and images:
        last = images[-1]
        return last.get("url", "") if isinstance(last, dict) else str(last)
    return ""


def _best_download(downloads):
    if not downloads:
        return ""

    if isinstance(downloads, list):
        for quality in ("320kbps", "320", "160kbps", "160", "96kbps", "96"):
            for item in downloads:
                if not isinstance(item, dict):
                    continue
                if quality in str(item.get("quality", "")).lower() and item.get("url"):
                    return item["url"]

        for item in reversed(downloads):
            if isinstance(item, dict) and item.get("url"):
                return item["url"]

    return downloads if isinstance(downloads, str) else ""


async def _spotify_to_query(query: str):
    if "spotify.com/track/" not in query and "spotify:track:" not in query:
        return query

    try:
        import base64
        import re

        track_id = re.search(r"(?:track/|spotify:track:)([A-Za-z0-9]+)", query).group(1)

        auth = base64.b64encode(
            f"{config.SPOTIFY_CLIENT_ID}:{config.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {auth}"},
                timeout=20,
            ) as resp:
                token_data = await resp.json()
                token = token_data.get("access_token")

            if not token:
                return query

            async with session.get(
                f"https://api.spotify.com/v1/tracks/{track_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            ) as resp:
                data = await resp.json()

        name = data.get("name", "")
        artists = " ".join(a.get("name", "") for a in data.get("artists", []))
        return f"{name} {artists}".strip() or query

    except Exception:
        return query


async def _jiosaavn(query: str):
    base = getattr(config, "SAAVN_API_URL", "https://saavn.sumit.co/api").rstrip("/")
    search_url = f"{base}/search/songs?query={quote_plus(query)}&limit=3"

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, timeout=30) as resp:
            data = await resp.json()

        results = data.get("data", {}).get("results") or data.get("results") or []

        for song in results:
            song_id = song.get("id")
            detail = song

            if song_id:
                async with session.get(f"{base}/songs?id={song_id}", timeout=30) as resp:
                    if resp.status == 200:
                        d = await resp.json()
                        dd = d.get("data")
                        if isinstance(dd, list) and dd:
                            detail = dd[0]
                        elif isinstance(dd, dict):
                            detail = dd

            audio = _best_download(detail.get("downloadUrl") or detail.get("download_url"))
            if not audio:
                continue

            title = detail.get("name") or detail.get("title") or "Unknown Track"
            artists = detail.get("primaryArtists") or detail.get("primary_artists") or ""
            if isinstance(artists, list):
                artists = ", ".join(a.get("name", "") for a in artists if isinstance(a, dict))

            return Track(
                title=f"{title} - {artists}".strip(" -"),
                url=audio,
                webpage_url=detail.get("url") or "",
                duration=_duration(detail.get("duration")),
                thumbnail=_best_image(detail.get("image")),
                source="JioSaavn",
            )

    raise Exception("JioSaavn not found")


async def _soundcloud(query: str):
    def _extract():
        opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "default_search": "scsearch1",
            "noplaylist": True,
            "cachedir": False,
            "socket_timeout": 20,
        }

        search = query if query.startswith(("http://", "https://")) else f"scsearch1:{query}"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search, download=False)

        if isinstance(info, dict) and info.get("entries"):
            info = next((x for x in info["entries"] if x), None)

        if not info:
            raise Exception("SoundCloud not found")

        return Track(
            title=info.get("title", "Unknown Track"),
            url=info.get("url"),
            webpage_url=info.get("webpage_url", ""),
            duration=_duration(info.get("duration")),
            thumbnail=info.get("thumbnail", ""),
            source="SoundCloud",
        )

    track = await asyncio.to_thread(_extract)
    if not track.url:
        raise Exception("SoundCloud no playable URL")
    return track


async def _audius(query: str):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.audius.co", timeout=20) as resp:
            hosts = await resp.json()

        host = (hosts.get("data") or ["https://discoveryprovider.audius.co"])[0]
        search_url = f"{host}/v1/tracks/search?query={quote_plus(query)}&app_name=JassMusic"

        async with session.get(search_url, timeout=30) as resp:
            data = await resp.json()

        results = data.get("data") or []
        if not results:
            raise Exception("Audius not found")

        item = results[0]
        track_id = item.get("id")
        stream_url = f"{host}/v1/tracks/{track_id}/stream?app_name=JassMusic"

        artwork = item.get("artwork") or {}

        return Track(
            title=f"{item.get('title', 'Unknown Track')} - {(item.get('user') or {}).get('name', '')}".strip(" -"),
            url=stream_url,
            webpage_url=item.get("permalink", ""),
            duration=_duration(item.get("duration")),
            thumbnail=artwork.get("1000x1000") or artwork.get("480x480") or artwork.get("150x150") or "",
            source="Audius",
        )


async def get_track(query: str, video: bool = False) -> Track:
    query = await _spotify_to_query(query)

    errors = []

    for name, source in (
        ("JioSaavn", _jiosaavn),
        ("SoundCloud", _soundcloud),
        ("Audius", _audius),
    ):
        try:
            return await source(query)
        except Exception as e:
            errors.append(f"{name}: {e}")

    raise Exception("Song not found on JioSaavn, SoundCloud, or Audius. Try shorter title + artist.")
