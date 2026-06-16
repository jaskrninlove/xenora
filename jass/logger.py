# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import logging, os
from logging.handlers import RotatingFileHandler
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[RotatingFileHandler("logs/jass.log", maxBytes=10_000_000, backupCount=5), logging.StreamHandler()],
)
for name in ["pyrogram", "pytgcalls", "httpx", "pymongo", "motor", "yt_dlp"]:
    logging.getLogger(name).setLevel(logging.WARNING)
LOGGER = logging.getLogger("JassMusic")
