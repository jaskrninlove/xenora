# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from motor.motor_asyncio import AsyncIOMotorClient

from jass.config import config
from jass import logger

mongo = AsyncIOMotorClient(config.MONGO_URI)

db = mongo.JassMusic

usersdb = db.users
chatsdb = db.chats
playlistdb = db.playlists
blacklistdb = db.blacklist
statsdb = db.stats
queuedb = db.queue
activevcdb = db.activevc


async def connect_db():
    await mongo.admin.command("ping")
    logger.info("MongoDB connected")