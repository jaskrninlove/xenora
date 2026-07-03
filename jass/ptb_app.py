# ==========================================================
# JassMusic - PTB UI Runner
# Copyright (c) 2026 Jass
# ==========================================================

from telegram.ext import Application

from jass.config import config
from jass.plugins.start import register_ptb
from jass.plugins.ptb_player import register_ptb_player


def build_ptb_app(pyro_app=None, call=None):
    ptb = Application.builder().token(config.BOT_TOKEN).build()
    register_ptb(ptb)

    if pyro_app and call:
        register_ptb_player(ptb, pyro_app, call)

    return ptb