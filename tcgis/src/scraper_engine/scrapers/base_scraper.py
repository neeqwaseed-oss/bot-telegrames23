"""
TCGIS - Base Scraper
Abstract base class for all scrapers
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScrapedGroup:
    """نموذج بيانات المجموعة المُجمعة"""
    title: str
    username: Optional[str] = None
    invite_link: Optional[str] = None
    description: Optional[str] = None
    member_count: Optional[int] = None
    country_code: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    source_name: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'username': self.username,
            'invite_link': self.invite_link,
            'description': self.description,
            'member_count': self.member_count,
            'country_code': self.country_code,
            'category': self.category,
            'language': self.language,
            'source_url': self.source_url,
            'source_name': self.source_name
        }


class BaseScraper(ABC):
    """الفئة الأساسية للجامعات"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"tcgis.scraper.{name}")
    
    @abstractmethod
    async def scrape(
        self,
        max_results: int = 1000,
        country_code: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> List[ScrapedGroup]:
        """
        جمع المجموعات
        
        Args:
            max_results: الحد الأقصى للنتائج
            country_code: فلتر الدولة
            category: فلتر الفئة
        
        Returns:
            قائمة بالمجموعات المُجمعة
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """اختبار الاتصال بالمصدر"""
        pass
    
    def parse_member_count(self, text: str) -> Optional[int]:
        """تحويل نص عدد الأعضاء إلى رقم"""
        if not text:
            return None
        
        text = text.lower().replace(',', '').replace(' ', '')
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
        
        try:
            for suffix, multiplier in multipliers.items():
                if suffix in text:
                    number = float(text.replace(suffix, ''))
                    return int(number * multiplier)
            return int(text)
        except ValueError:
            return None
    
    def extract_username(self, url: str) -> Optional[str]:
        """استخراج اسم المستخدم من رابط Telegram"""
        if not url:
            return None
        
        import re
        patterns = [
            r't\.me/([a-zA-Z0-9_]{5,32})',
            r'telegram\.me/([a-zA-Z0-9_]{5,32})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def deduplicate_results(self, groups: List[ScrapedGroup]) -> List[ScrapedGroup]:
        """إزالة التكرارات من النتائج"""
        seen = set()
        unique = []
        
        for group in groups:
            key = group.username or group.invite_link
            if key and key not in seen:
                seen.add(key)
                unique.append(group)
        
        return unique
