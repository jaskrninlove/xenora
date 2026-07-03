# ==========================================================
# JassMusic - Hybrid Keyboards
# Copyright (c) 2026 Jass
# ==========================================================

# PTB buttons = premium colored start/help UI
# Pyrogram buttons = player controls for PyTgCalls callbacks

from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from pyrogram.types import InlineKeyboardButton as PyroBtn, InlineKeyboardMarkup as PyroMarkup

from .premium_ptb import PREMIUM, FALLBACK


SUPPORT_URL = "https://t.me/Xenoraorg"
UPDATES_URL = "https://t.me/Xenoraorg"
OWNER_URL = "https://t.me/imceobiitxh"


def pbtn(text: str, *, callback_data=None, url=None, style=None, icon_name=None) -> Btn:
    api_kwargs = {}

    if style:
        api_kwargs["style"] = style

    if icon_name and PREMIUM.get(icon_name):
        api_kwargs["icon_custom_emoji_id"] = PREMIUM[icon_name]

    return Btn(
        text=text,
        callback_data=callback_data,
        url=url,
        api_kwargs=api_kwargs or None,
    )


def ibtn(*, callback_data=None, url=None, style=None, icon_name: str) -> Btn:
    """Icon-only button: shows just the custom premium icon, no duplicate
    fallback emoji as text. Telegram requires non-empty button text, so a
    single space is used as an invisible placeholder."""
    return pbtn(" ", callback_data=callback_data, url=url, style=style, icon_name=icon_name)


def start_buttons(username: str = None):
    bot_username = username or "LunariaMusicBot"

    return Markup([
        [
            pbtn(
                "Add Me In Your Chat",
                url=f"https://t.me/{bot_username}?startgroup=true",
                style="success",
                icon_name="add",
            )
        ],
        [
            pbtn(
                "Help & Commands",
                callback_data="help:main",
                style="primary",
                icon_name="music",
            )
        ],
        [
            pbtn(
                "Support",
                url=SUPPORT_URL,
                style="primary",
                icon_name="support",
            ),
            pbtn(
                "Updates",
                url=UPDATES_URL,
                style="primary",
                icon_name="updates",
            ),
        ],
        [
            pbtn(
                "Owner",
                url=OWNER_URL,
                style="danger",
                icon_name="owner",
            )
        ],
    ])


def help_buttons(page: str = "main"):
    return Markup([
        [
            pbtn("Play", callback_data="help:play", style="primary", icon_name="play"),
            pbtn("Admin", callback_data="help:admin", style="primary", icon_name="adimin"),
        ],
        [
            pbtn("Owner", callback_data="help:owner", style="danger", icon_name="owner"),
            pbtn("Tools", callback_data="help:tools", style="primary", icon_name="tools"),
        ],
        [
            pbtn("Download", callback_data="help:download", style="success", icon_name="download"),
            pbtn("Settings", callback_data="help:settings", style="primary", icon_name="settings"),
        ],
        [
            pbtn("Home", callback_data="home", style="success", icon_name="home"),
        ],
    ])


def group_start_buttons(username: str = None):
    bot_username = username or "LunariaMusicBot"

    return Markup([
        [
            pbtn(
                "Open Private",
                url=f"https://t.me/{bot_username}?start=group",
                style="success",
                icon_name="bot",
            )
        ],
        [
            pbtn("Support", url=SUPPORT_URL, style="primary", icon_name="support"),
            pbtn("Updates", url=UPDATES_URL, style="primary", icon_name="updates"),
        ],
    ])


def player_buttons_ptb(progress: str = "00:00 ◉──────────── 00:00"):
    return Markup([
        [
            ibtn(callback_data="resume", style="success", icon_name="jkjk"),
            ibtn(callback_data="pause", style="primary", icon_name="ckck"),
            ibtn(callback_data="replay", style="primary", icon_name="resume"),
            ibtn(callback_data="skip", style="primary", icon_name="pkpk"),
            ibtn(callback_data="stop", style="danger", icon_name="dkdk"),
        ],
        [pbtn(progress, callback_data="progress", style="primary")],
        [pbtn("Close", callback_data="delete_player", style="danger", icon_name="close")],
    ])


def player_close_button_ptb():
    return Markup([
        [pbtn("Close", callback_data="delete_player", style="danger", icon_name="close")]
    ])

def player_close_button():
    """Pyrogram-native close button — for use with pyrogram message.reply_text/
    edit_text (e.g. play.py's premium_reply/premium_edit). Do NOT pass the PTB
    Markup (player_close_button_ptb) into a pyrogram call, it will crash with
    AttributeError: 'InlineKeyboardMarkup' object has no attribute 'write'."""
    return PyroMarkup([
        [PyroBtn("❌ Close", callback_data="delete_player")]
    ])