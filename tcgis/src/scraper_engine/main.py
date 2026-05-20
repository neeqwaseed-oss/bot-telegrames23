"""
TCGIS - Scraper Engine
Multi-source group link scraper with rate limiting and proxy rotation
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from shared.clients.postgres_client import get_db_session
from shared.clients.redis_client import redis_client
from shared.clients.elasticsearch_client import es_client
from shared.models.database_models import Group, Source, Country

from scraper_engine.scrapers.tgstat_scraper import TGStatScraper
from scraper_engine.scrapers.google_scraper import GoogleScraper
from scraper_engine.scrapers.directory_scraper import DirectoryScraper
from scraper_engine.utils.proxy_manager import ProxyManager
from scraper_engine.utils.rate_limiter import RateLimiter


logging.basicConfig(level=logging.INFO)
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


class ScraperEngine:
    """محرك الجمع الرئيسي"""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter()
        self.scrapers = {
            'tgstat': TGStatScraper(),
            'google': GoogleScraper(),
            'directory': DirectoryScraper()
        }
        self.results: List[ScrapedGroup] = []
    
    async def run(self, sources: Optional[List[str]] = None):
        """
        تشغيل عملية الجمع
        
        Args:
            sources: قائمة المصادر (None = جميع المصادر)
        """
        sources_to_run = sources or list(self.scrapers.keys())
        
        logger.info(f"🚀 Starting scraper engine for sources: {sources_to_run}")
        
        tasks = []
        for source_name in sources_to_run:
            scraper = self.scrapers.get(source_name)
            if scraper:
                task = asyncio.create_task(
                    self._scrape_source(source_name, scraper)
                )
                tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # معالجة النتائج
        await self._process_results()
        
        logger.info(f"✅ Scraping completed. Total groups found: {len(self.results)}")
    
    async def _scrape_source(self, source_name: str, scraper):
        """جمع من مصدر واحد"""
        logger.info(f"🔍 Scraping from {source_name}...")
        
        try:
            # التحقق من Rate Limit
            allowed, remaining = await self.rate_limiter.check_limit(source_name)
            if not allowed:
                logger.warning(f"⏳ Rate limit exceeded for {source_name}")
                return
            
            # جمع البيانات
            raw_groups = await scraper.scrape(max_results=1000)
            
            # تحويل إلى ScrapedGroup
            for group_data in raw_groups:
                scraped = ScrapedGroup(
                    title=group_data.title or 'Unknown',
                    username=group_data.username,
                    invite_link=group_data.invite_link,
                    description=group_data.description,
                    member_count=group_data.member_count,
                    country_code=group_data.country_code,
                    category=group_data.category,
                    language=group_data.language,
                    source_url=group_data.source_url,
                    source_name=source_name
                )
                self.results.append(scraped)
            
            logger.info(f"✅ {source_name}: Found {len(raw_groups)} groups")
            
        except Exception as e:
            logger.error(f"❌ Error scraping {source_name}: {e}")
    
    async def _process_results(self):
        """معالجة النتائج وحفظها"""
        if not self.results:
            logger.info("ℹ️ No results to process")
            return
        
        # إزالة التكرارات
        unique_groups = self._deduplicate(self.results)
        logger.info(f"🔄 After deduplication: {len(unique_groups)} unique groups")
        
        # حفظ في قاعدة البيانات
        saved_count = 0
        async with get_db_session() as session:
            for group in unique_groups:
                try:
                    # التحقق من عدم التكرار
                    from sqlalchemy import select
                    existing_result = await session.execute(
                        select(Group).where(
                            (Group.username == group.username) | 
                            (Group.invite_link == group.invite_link)
                        )
                    )
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        continue
                    
                    # إنشاء سجل جديد
                    new_group = Group(
                        username=group.username,
                        invite_link=group.invite_link,
                        title=group.title,
                        description=group.description,
                        member_count=group.member_count,
                        language_detected=group.language,
                        status='pending',  # pending until verified
                        source_url=group.source_url,
                        discovered_by=group.source_name,
                        discovered_at=datetime.utcnow()
                    )
                    
                    # البحث عن الدولة
                    if group.country_code:
                        country_result = await session.execute(
                            select(Country).where(Country.code == group.country_code)
                        )
                        country = country_result.scalar_one_or_none()
                        if country:
                            new_group.country_id = country.id
                    
                    session.add(new_group)
                    saved_count += 1
                    
                    # حفظ كل 100 سجل
                    if saved_count % 100 == 0:
                        await session.commit()
                        logger.info(f"💾 Saved {saved_count} groups so far...")
                
                except Exception as e:
                    logger.error(f"❌ Error saving group: {e}")
                    continue
            
            # الحفظ النهائي
            await session.commit()
        
        logger.info(f"✅ Saved {saved_count} new groups to database")
        
        # إرسال للمعالج
        if saved_count > 0:
            await redis_client.push_queue('process_queue', {
                'type': 'new_groups',
                'count': saved_count,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def _deduplicate(self, groups: List[ScrapedGroup]) -> List[ScrapedGroup]:
        """إزالة التكرارات"""
        seen = set()
        unique = []
        
        for group in groups:
            key = group.username or group.invite_link
            if key and key not in seen:
                seen.add(key)
                unique.append(group)
        
        return unique


async def main():
    """الدالة الرئيسية"""
    engine = ScraperEngine()
    
    # تشغيل الجمع
    await engine.run(sources=['tgstat', 'google', 'directory'])
    
    # جدولة الجمع التالي
    await redis_client.set(
        'scraper:last_run',
        datetime.utcnow().isoformat(),
        expire=3600  # 1 hour
    )


if __name__ == '__main__':
    asyncio.run(main())
