"""
TCGIS - Rate Limiter
Rate limiting for scraping operations
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict

from shared.clients.redis_client import redis_client


logger = logging.getLogger(__name__)


class RateLimiter:
    """محدد معدل الطلبات للجمع"""
    
    def __init__(self):
        self.local_limits: Dict[str, Dict] = defaultdict(lambda: {
            'last_request': 0,
            'requests': 0,
            'window_start': time.time()
        })
        self.default_delay = 2  # ثواني بين الطلبات
    
    async def check_limit(self, source: str) -> Tuple[bool, int]:
        """
        التحقق من حد المعدل لمصدر معين
        
        Returns:
            (allowed, remaining_requests)
        """
        # استخدام Redis للتحقق العام
        try:
            key = f"scraper:rate_limit:{source}"
            allowed, remaining = await redis_client.check_rate_limit(
                key,
                max_requests=100,  # 100 طلب لكل نافذة
                window=60  # نافذة 60 ثانية
            )
            return allowed, remaining
        except Exception as e:
            logger.warning(f"⚠️ Redis rate limit check failed: {e}, using local limit")
            return self._check_local_limit(source)
    
    def _check_local_limit(self, source: str) -> Tuple[bool, int]:
        """التحقق المحلي من الحد"""
        now = time.time()
        data = self.local_limits[source]
        
        # إعادة تعيين النافذة
        if now - data['window_start'] > 60:
            data['requests'] = 0
            data['window_start'] = now
        
        # التحقق من الحد
        if data['requests'] >= 100:
            return False, 0
        
        data['requests'] += 1
        data['last_request'] = now
        
        return True, 100 - data['requests']
    
    async def wait_if_needed(self, source: str):
        """الانتظار إذا لزم الأمر"""
        data = self.local_limits[source]
        elapsed = time.time() - data['last_request']
        
        if elapsed < self.default_delay:
            wait_time = self.default_delay - elapsed
            logger.debug(f"⏳ Rate limit: waiting {wait_time:.1f}s for {source}")
            await asyncio.sleep(wait_time)
    
    async def acquire(self, source: str) -> bool:
        """محاولة الحصول على إذن للطلب"""
        await self.wait_if_needed(source)
        allowed, _ = await self.check_limit(source)
        return allowed
