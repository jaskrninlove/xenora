# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import asyncio
from pyrogram import idle

from . import app, assistant, call, logger
from .database.mongo import connect_db
from .plugins import load_plugins
from .core.logger import startup_log


async def start_bot():
    await connect_db()

    load_plugins()
    logger.info("Plugins loaded")

    await app.start()
    logger.info("Bot client started")

    await assistant.start()
    logger.info("Assistant client started")

    await call.start()
    logger.info("PyTgCalls started")

    await startup_log()

    logger.info("JassMusic is running...")
    await idle()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())