"""
TCGIS - Proxy Manager
Manage proxy rotation for scraping
"""

import os
import random
import logging
from typing import Optional, List


logger = logging.getLogger(__name__)


class ProxyManager:
    """مدير البروكسي للتناوب بين البروكسيات"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.current_index = 0
        self._load_proxies()
    
    def _load_proxies(self):
        """تحميل البروكسيات من المتغير البيئي"""
        proxy_pool = os.getenv('PROXY_POOL', '')
        if proxy_pool:
            self.proxies = [p.strip() for p in proxy_pool.split(',') if p.strip()]
            logger.info(f"✅ Loaded {len(self.proxies)} proxies")
        else:
            logger.warning("⚠️ No proxies configured")
    
    async def get_proxy(self) -> Optional[str]:
        """الحصول على بروكسي عشوائي"""
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        return proxy
    
    def get_next_proxy(self) -> Optional[str]:
        """الحصول على البروكسي التالي بالتناوب"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def remove_proxy(self, proxy: str):
        """إزالة بروكسي معطل"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.warning(f"🗑️ Removed dead proxy: {proxy}")
    
    @property
    def has_proxies(self) -> bool:
        """التحقق من توفر بروكسيات"""
        return len(self.proxies) > 0
    
    @property
    def proxy_count(self) -> int:
        """عدد البروكسيات المتاحة"""
        return len(self.proxies)
