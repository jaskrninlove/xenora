# ==========================================================

# JassMusic

# Copyright (c) 2026 Jass

# Proprietary Software. Unauthorized copying, modification, distribution, or resale of this source code is strictly prohibited.

# Developed by Jass (Jaskaran Singh)

# © 2026 All Rights Reserved.

# ==========================================================


from motor.motor_asyncio import AsyncIOMotorClient
from jass.config import config


class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        if self.db is not None:
            return
        self.client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.MONGO_DB_NAME]
        await self.client.admin.command("ping")

    # ── Users ─────────────────────────────────────────────────────────────────

    async def add_user(self, user_id: int, name: str = ""):
        await self.connect()
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"name": name}, "$inc": {"starts": 1}},
            upsert=True,
        )

    async def get_all_users(self) -> list[int]:
        await self.connect()
        return [doc["_id"] async for doc in self.db.users.find({}, {"_id": 1})]
    
    async def add_chat(self, chat_id: int, title: str = ""):
       await self.connect()
       await self.db.chats.update_one(
        {"_id": chat_id},
        {"$set": {"title": title}},
        upsert=True,
    )

    async def get_all_chats(self):
       await self.connect()
       return [doc["_id"] async for doc in self.db.chats.find({}, {"_id": 1})]

    async def stats(self):
        await self.connect()
        return {
            "users": await self.db.users.count_documents({}),
            "groups": await self.db.chats.count_documents({}),
            "plays": await self.db.plays.count_documents({}),
        }

    async def log_play(self, chat_id: int, user_id: int, title: str):
        await self.connect()
        await self.db.plays.insert_one(
            {"chat_id": chat_id, "user_id": user_id, "title": title}
        )

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def auth_user(self, chat_id: int, user_id: int):
        await self.connect()
        await self.db.auth.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"users": user_id}},
            upsert=True,
        )

    async def unauth_user(self, chat_id: int, user_id: int):
        await self.connect()
        await self.db.auth.update_one(
            {"chat_id": chat_id},
            {"$pull": {"users": user_id}},
        )

    async def get_auth_users(self, chat_id: int) -> list[int]:
        await self.connect()
        doc = await self.db.auth.find_one({"chat_id": chat_id})
        return doc.get("users", []) if doc else []

    async def is_auth(self, chat_id: int, user_id: int) -> bool:
        return user_id in await self.get_auth_users(chat_id)

    # ── Blacklist ─────────────────────────────────────────────────────────────

    async def blacklist_chat(self, chat_id: int):
        await self.connect()
        await self.db.blacklist.update_one(
            {"_id": chat_id}, {"$set": {"_id": chat_id}}, upsert=True
        )

    async def whitelist_chat(self, chat_id: int):
        await self.connect()
        await self.db.blacklist.delete_one({"_id": chat_id})

    async def is_blacklisted(self, chat_id: int) -> bool:
        await self.connect()
        return await self.db.blacklist.find_one({"_id": chat_id}) is not None

    # ── Global Ban ────────────────────────────────────────────────────────────

    async def gban_user(self, user_id: int, reason: str = ""):
        await self.connect()
        await self.db.gbans.update_one(
            {"_id": user_id},
            {"$set": {"reason": reason}},
            upsert=True,
        )

    async def ungban_user(self, user_id: int):
        await self.connect()
        await self.db.gbans.delete_one({"_id": user_id})

    async def is_gbanned(self, user_id: int) -> bool:
        await self.connect()
        return await self.db.gbans.find_one({"_id": user_id}) is not None

    async def get_gban(self, user_id: int) -> dict | None:
        await self.connect()
        return await self.db.gbans.find_one({"_id": user_id})

    # ── Maintenance ───────────────────────────────────────────────────────────

    async def set_maintenance(self, state: bool):
        await self.connect()
        await self.db.config.update_one(
            {"_id": "maintenance"},
            {"$set": {"enabled": state}},
            upsert=True,
        )

    async def is_maintenance(self) -> bool:
        await self.connect()
        doc = await self.db.config.find_one({"_id": "maintenance"})
        return doc.get("enabled", False) if doc else False

    # ── Settings ──────────────────────────────────────────────────────────────

    async def get_settings(self, chat_id: int) -> dict:
        await self.connect()
        doc = await self.db.settings.find_one({"_id": chat_id})
        if doc:
            doc.pop("_id", None)
        return doc or {
            "playmode": "queue",
            "stream":   "audio",
            "lang":     "en",
        }

    async def set_setting(self, chat_id: int, key: str, value):
        await self.connect()
        await self.db.settings.update_one(
            {"_id": chat_id},
            {"$set": {key: value}},
            upsert=True,
        )


db = Database()
