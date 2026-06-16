# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import re
from ..config import config

async def to_search_query(url: str) -> str:
    # Free fallback: extract readable slug; if Spotify credentials exist, metadata can be added later.
    slug = url.split("?")[0].rstrip("/").split("/")[-1]
    readable = re.sub(r"[-_]+", " ", slug)
    return readable if readable and not re.fullmatch(r"[A-Za-z0-9]+", readable) else url
