# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_buttons(username: str = None):
    bot_username = username or "LunariaMusicBot"

    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("𐙚 Add Me in Your Chat 𐙚", url=f"https://t.me/{bot_username}?startgroup=true")],
            [
                InlineKeyboardButton("Help & Commands", callback_data="help:main"),
            ],
            [
                InlineKeyboardButton("Support Chat", url="https://t.me/Xenoraorg"),
                InlineKeyboardButton("Updates", url="https://t.me/Xenoraorg")
            ],
            [
                InlineKeyboardButton("Owner", url="https://t.me/imceobiitxh"),
            ],
        ]
    )


def help_buttons(page: str = "main"):
    rows = [
        [
            InlineKeyboardButton("Play", callback_data="help:play"),
            InlineKeyboardButton("Admin", callback_data="help:admin"),
        ],
        [
            InlineKeyboardButton("Owner", callback_data="help:owner"),
            InlineKeyboardButton("Tools", callback_data="help:tools"),
        ],
        [
            InlineKeyboardButton("Download", callback_data="help:download"),
            InlineKeyboardButton("Settings", callback_data="help:settings"),
        ],
        [InlineKeyboardButton("𐙚 Home 𐙚", callback_data="home")],
    ]

    # Highlight the active page button with a dot prefix
    page_map = {
        "play":     (0, 0),
        "admin":    (0, 1),
        "owner":    (1, 0),
        "tools":    (1, 1),
        "download": (2, 0),
        "settings": (2, 1),
    }
    if page in page_map:
        r, c = page_map[page]
        btn = rows[r][c]
        rows[r][c] = InlineKeyboardButton(
            f"» {btn.text} «",
            callback_data=btn.callback_data,
        )

    return InlineKeyboardMarkup(rows)


def player_buttons(progress: str = "00:00 ◉──────────── 00:00"):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("▷", callback_data="resume"),
                InlineKeyboardButton("Ⅱ", callback_data="pause"),
                InlineKeyboardButton("↻", callback_data="replay"),
                InlineKeyboardButton("▸▸|", callback_data="skip"),
                InlineKeyboardButton("□", callback_data="stop"),
            ],
            [InlineKeyboardButton(progress, callback_data="progress")],
            [
            InlineKeyboardButton("✃ Close ✃", callback_data="delete_player")
            ]
        ]
    )

def player_close_button():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✃ Close ✃", callback_data="delete_player")
            ]
        ]
    )

def group_start_buttons(username: str):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Add Me", url=f"https://t.me/{username}?startgroup=true"),
                InlineKeyboardButton("Support", url="https://t.me/Xenoraorg"),
            ]
        ]
    )