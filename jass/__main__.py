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
from .ptb_app import build_ptb_app


async def start_bot():
    await connect_db()

    load_plugins()
    logger.info("Pyrogram plugins loaded")

    ptb = build_ptb_app(app, call)

    await ptb.initialize()
    await ptb.start()
    await ptb.updater.start_polling()
    logger.info("PTB premium UI started")

    await app.start()
    logger.info("Bot client started")

    await assistant.start()
    logger.info("Assistant client started")

    await call.start()
    logger.info("PyTgCalls started")

    await startup_log()

    logger.info("JassMusic is running...")

    try:
        await idle()
    finally:
        logger.info("Stopping JassMusic...")

        await ptb.updater.stop()
        await ptb.stop()
        await ptb.shutdown()

        await call.stop()
        await assistant.stop()
        await app.stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())