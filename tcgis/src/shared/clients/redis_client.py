"""
TCGIS - Redis Client
Cache and queue management
"""

import os
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis


# إعدادات الاتصال
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


class RedisClient:
    """عميل Redis للتخزين المؤقت والطوابير"""
    
    def __init__(self):
        self._pool = None
        self._client = None
    
    async def connect(self):
        """إنشاء الاتصال"""
        self._pool = redis.ConnectionPool.from_url(
            REDIS_URL,
            max_connections=int(os.getenv('REDIS_POOL_SIZE', 50)),
            decode_responses=True
        )
        self._client = redis.Redis(connection_pool=self._pool)
        await self._client.ping()
        print("✅ Redis connected successfully")
    
    async def disconnect(self):
        """إغلاق الاتصال"""
        if self._pool:
            await self._pool.disconnect()
            print("✅ Redis disconnected")
    
    async def get(self, key: str) -> Optional[str]:
        """الحصول على قيمة نصية"""
        return await self._client.get(key)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """الحصول على قيمة JSON"""
        value = await self._client.get(key)
        return json.loads(value) if value else None
    
    async def set(
        self, 
        key: str, 
        value: Union[str, bytes, int, float],
        expire: Optional[int] = None
    ) -> bool:
        """تخزين قيمة"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self._client.set(key, value, ex=expire)
    
    async def set_json(
        self, 
        key: str, 
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """تخزين قيمة JSON"""
        return await self.set(key, json.dumps(value), expire)
    
    async def delete(self, key: str) -> int:
        """حذف مفتاح"""
        return await self._client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """التحقق من وجود مفتاح"""
        return await self._client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """تعيين وقت انتهاء"""
        return await self._client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """الحصول على الوقت المتبقي"""
        return await self._client.ttl(key)
    
    # Queue Operations
    async def push_queue(self, queue_name: str, value: Any) -> int:
        """إضافة إلى الطابور"""
        return await self._client.lpush(queue_name, json.dumps(value))
    
    async def pop_queue(self, queue_name: str, timeout: int = 0) -> Optional[Any]:
        """سحب من الطابور (blocking)"""
        result = await self._client.brpop(queue_name, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None
    
    async def queue_length(self, queue_name: str) -> int:
        """طول الطابور"""
        return await self._client.llen(queue_name)
    
    # Rate Limiting
    async def check_rate_limit(
        self, 
        key: str, 
        max_requests: int, 
        window: int
    ) -> tuple[bool, int]:
        """
        التحقق من Rate Limit
        Returns: (allowed, remaining)
        """
        pipe = self._client.pipeline()
        now = await self._client.time()
        current_time = int(now[0])
        window_start = current_time - window
        
        # إزالة الطلبات القديمة
        pipe.zremrangebyscore(key, 0, window_start)
        # عدد الطلبات الحالية
        pipe.zcard(key)
        # إضافة الطلب الحالي
        pipe.zadd(key, {str(current_time): current_time})
        # تعيين وقت انتهاء
        pipe.expire(key, window)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count >= max_requests:
            # إزالة الطلب المضاف لأنه تجاوز الحد
            await self._client.zrem(key, str(current_time))
            return False, 0
        
        return True, max_requests - current_count - 1
    
    # Caching Patterns
    async def cache_get_or_set(
        self,
        key: str,
        factory,
        expire: int = 300
    ) -> Any:
        """الحصول من الكاش أو إنشاء"""
        cached = await self.get_json(key)
        if cached is not None:
            return cached
        
        value = await factory()
        await self.set_json(key, value, expire)
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """إبطال الكاش حسب النمط"""
        keys = []
        async for key in self._client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await self._client.delete(*keys)
        return 0


# Instance global
redis_client = RedisClient()
