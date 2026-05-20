"""
TCGIS - Telegram Global Search Client
Connects to Telegram API using a User Session for Global Search
"""

import os
import asyncio
import logging
from typing import List, Dict, Any
from pyrogram import Client
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

class TelegramSearchClient:
    def __init__(self):
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.session_string = os.getenv("TELEGRAM_SESSION")
        self.client = None
        
    async def connect(self):
        """تهيئة العميل والاتصال"""
        if not self.api_id or not self.api_hash:
            logger.warning("⚠️ API_ID or API_HASH missing. Global search disabled.")
            return False
            
        try:
            # استخدام Session String للتشغيل على السيرفر بدون تدخل يدوي
            if self.session_string:
                self.client = Client(
                    "tg_search_session",
                    api_id=self.api_id,
                    api_hash=self.api_hash,
                    session_string=self.session_string,
                    in_memory=True
                )
            else:
                # للمرة الأولى محلياً لإنشاء الجلسة
                self.client = Client(
                    "tg_search_session",
                    api_id=self.api_id,
                    api_hash=self.api_hash,
                    workdir="/tmp"
                )
            
            await self.client.start()
            logger.info("✅ Telegram Global Search Client connected")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect Telegram Search Client: {e}")
            return False

    async def search_global(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """البحث العالمي في سيرفرات تيليجرام"""
        if not self.client:
            return []
            
        results = []
        try:
            # البحث عن المجموعات والقنوات العامة
            async for dialog in self.client.search_global(query, limit=limit):
                chat = dialog
                # نفلتر فقط المجموعات والقنوات
                if chat.type in ["supergroup", "channel"]:
                    results.append({
                        "title": chat.title,
                        "username": chat.username,
                        "members": getattr(chat, 'members_count', 'غير معروف'),
                        "link": f"https://t.me/{chat.username}" if chat.username else None,
                        "type": "مجموعة" if chat.type == "supergroup" else "قناة"
                    })
            return results
        except FloodWait as e:
            logger.warning(f"⚠️ Telegram FloodWait: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.search_global(query, limit)
        except Exception as e:
            logger.error(f"❌ Error searching global Telegram: {e}")
            return []

    async def disconnect(self):
        """قطع الاتصال"""
        if self.client:
            await self.client.stop()

tg_search_client = TelegramSearchClient()
