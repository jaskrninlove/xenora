# ==========================================================
# JassMusic - Premium Emoji Engine
# Copyright (c) 2026 Jass
# ==========================================================

import re
from pyrogram.enums import ParseMode

TOKEN_RE = re.compile(r":([a-zA-Z0-9_]+):")

PREMIUM = {
    "play": "5271810272640643747",
    "pause": "5298499667569425533",
    "skip": "5249244862359812334",
    "stop": "5220037761897085778",
    "close": "6242430400015115368",
    "music": "6242065804536324467",
    "download": "6241991681990729791",
    "video": "6242118843087462180",
    "thumb": "6239892082933112209",
    "settings": "6242135537625341249",
    "tools": "6240245537266737364",
    "stats": "5291873529464122510",
    "ping": "5256169350368353876",
    "owner": "5260567255145539253",
    "support": "5262922516426420894",
    "updates": "5280569974404966639",
    "add": "5262671999573977569",
    "home": "5256227233642605352",
    "back": "5262671999573977569",
    "success": "5285338659413846416",
    "error": "5285238101344544669",
    "warning": "5258500400918587241",
    "queue": "6294070144729619431",
    "active": "6102388765081212318",
    "rocket": "5255858639549251782",
    "star": "5420353563408741206",
    "gift": "5422516277010774456",
    "bot": "5422369251690298040",

    "chat": "5442872991769707734",
    "target": "5440910346334255336",
    "chart": "5440833702642857683",
    "mail": "5253821918812862724",
    "sad": "5197498864449371267",
    "lock": "5197448703526323358",
    "key": "5454359873212923789",
    "receipt": "5456145097844340698",
    "signal": "5197209727251004682",
    "battery": "5208744089557678654",
    "profile": "5208902681225083086",
    "search": "5197449768678212298",
    "time": "5204063760616013585",
    "language": "5204063760616013585",
    "shuffle": "5260371447586502532",
    "loop": "5296631769112525274",
    "volume": "5256041592271157291",
    "delete": "5472427031100667803",
    "qqqq": "6240242444890283576",

    "playmode": "6118209143972040877",

}

FALLBACK = {
    "play": "▶️",
    "pause": "⏸",
    "skip": "⏭",
    "stop": "⏹",
    "close": "❌",
    "music": "🎶",
    "download": "⬇️",
    "video": "📺",
    "thumb": "🖼",
    "settings": "⚙️",
    "tools": "🔧",
    "stats": "🖥",
    "ping": "ℹ️",
    "owner": "👤",
    "support": "🔗",
    "updates": "📰",
    "add": "➕",
    "home": "↩️",
    "back": "⬅️",
    "success": "✅",
    "error": "❌",
    "warning": "❗️",
    "queue": "🗂",
    "active": "🎶",
    "rocket": "✈️",
    "star": "⭐️",
    "gift": "🎁",
    "bot": "🤖",

    "chat": "💬",
    "target": "🎯",
    "chart": "📊",
    "mail": "📩",
    "sad": "🥺",
    "lock": "🔒",
    "key": "🔑",
    "receipt": "🧾",
    "signal": "📡",
    "battery": "🔋",
    "profile": "👤",
    "search": "🔎",
    "time": "🕒",
    "language": "🔣",
    "shuffle": "🔀",
    "loop": "🔁",
    "volume": "🔊",
    "delete": "🗑",
}


def pe(name: str, fallback: str = "✨") -> str:
    emoji_id = PREMIUM.get(name)
    fb = FALLBACK.get(name, fallback)

    if emoji_id:
        return f'<emoji id="{emoji_id}">{fb}</emoji>'

    return fb


def render(text: str) -> str:
    def repl(match):
        return pe(match.group(1))

    return TOKEN_RE.sub(repl, text or "")


async def reply(message, text: str, **kwargs):
    kwargs.pop("parse_mode", None)
    kwargs.pop("entities", None)
    kwargs.pop("caption_entities", None)

    return await message.reply_text(
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def send(client, chat_id, text: str, **kwargs):
    kwargs.pop("parse_mode", None)
    kwargs.pop("entities", None)
    kwargs.pop("caption_entities", None)

    return await client.send_message(
        chat_id,
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def edit(message, text: str, **kwargs):
    kwargs.pop("parse_mode", None)
    kwargs.pop("entities", None)
    kwargs.pop("caption_entities", None)

    return await message.edit_text(
        render(text),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def reply_photo(message, photo, caption: str, **kwargs):
    kwargs.pop("parse_mode", None)
    kwargs.pop("entities", None)
    kwargs.pop("caption_entities", None)

    return await message.reply_photo(
        photo=photo,
        caption=render(caption),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )


async def reply_animation(message, animation, caption: str, **kwargs):
    kwargs.pop("parse_mode", None)
    kwargs.pop("entities", None)
    kwargs.pop("caption_entities", None)

    return await message.reply_animation(
        animation=animation,
        caption=render(caption),
        parse_mode=ParseMode.HTML,
        **kwargs,
    )

async def reply_emoji(message, name: str = "playmode"):
    return await message.reply_text(
        pe(name) + "\u200b",
        parse_mode=ParseMode.HTML,
    )