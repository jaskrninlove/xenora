# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from .users import get_users_count
from .chats import get_chats_count
from .activevc import get_active_vc_count


async def get_stats():
    return {
        "users": await get_users_count(),
        "groups": await get_chats_count(),
        "active_vc": await get_active_vc_count(),
    }