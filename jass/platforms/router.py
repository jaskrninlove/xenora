# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from . import spotify, soundcloud, generic, youtube_music
from ..core import youtube

async def resolve(query: str):
    q = query.strip()
    if "open.spotify.com" in q:
        q = await spotify.to_search_query(q)
    elif "soundcloud.com" in q:
        return await soundcloud.resolve(q)
    elif q.lower().startswith(("ytm:", "youtube music:")):
        q = youtube_music.normalize(q)
    elif q.startswith("http") and "youtube" not in q and "youtu.be" not in q:
        return await generic.resolve(q)
    return await youtube.resolve(q)
