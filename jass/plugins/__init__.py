# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

import importlib

from jass import logger, app, call

PLUGINS = [
    "jass.plugins.start",
    "jass.plugins.play",
    "jass.plugins.owner",
    "jass.plugins.admin",
    "jass.plugins.group_events",
    "jass.plugins.download",
    "jass.plugins.middleware",
    "jass.plugins.playback",
    "jass.plugins.settings",
    "jass.plugins.tools",
    "jass.plugins.broadcast",
    "jass.plugins.logger_cmd",
]


def load_plugins():
    for plugin in PLUGINS:
        try:
            module = importlib.import_module(plugin)

            if hasattr(module, "register"):
                module.register(app, call)

            logger.info(f"Loaded plugin: {plugin}")

        except Exception as e:
            logger.exception(f"Failed to load plugin {plugin}: {e}")