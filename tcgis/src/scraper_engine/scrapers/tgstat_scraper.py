"""
TCGIS - TGStat Scraper
Scrape public groups from TGStat.com
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from scraper_engine.scrapers.base_scraper import BaseScraper, ScrapedGroup


logger = logging.getLogger(__name__)

BASE_URL = "https://tgstat.com"
SEARCH_URL = "https://tgstat.com/search"


class TGStatScraper(BaseScraper):
    """جامع TGStat"""
    
    def __init__(self):
        super().__init__("tgstat")
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    async def _init_session(self):
        """تهيئة الجلسة"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def _close_session(self):
        """إغلاق الجلسة"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape(
        self,
        max_results: int = 1000,
        country_code: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> List[ScrapedGroup]:
        """
        جمع المجموعات من TGStat
        
        Args:
            max_results: الحد الأقصى للنتائج
            country_code: فلتر الدولة
            category: فلتر الفئة
        """
        await self._init_session()
        results = []
        
        try:
            # البحث عن المجموعات
            page = 1
            while len(results) < max_results:
                groups = await self._fetch_page(page, country_code, category)
                
                if not groups:
                    break
                
                results.extend(groups)
                self.logger.info(f"📄 TGStat page {page}: Found {len(groups)} groups (total: {len(results)})")
                
                page += 1
                
                # تأخير بين الطلبات
                await asyncio.sleep(2)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"❌ TGStat scraping error: {e}")
            return results
        
        finally:
            await self._close_session()
    
    async def test_connection(self) -> bool:
        """اختبار الاتصال"""
        try:
            await self._init_session()
            async with self.session.get(BASE_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _fetch_page(
        self,
        page: int,
        country_code: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[ScrapedGroup]:
        """جلب صفحة واحدة"""
        params = {
            'q': 'group',
            'type': 'groups',
            'page': page
        }
        
        if country_code:
            params['country'] = country_code
        
        if category:
            params['category'] = category
        
        try:
            async with self.session.get(
                SEARCH_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    self.logger.warning(f"⚠️ TGStat returned status {response.status}")
                    return []
                
                html = await response.text()
                return self._parse_page(html)
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching page {page}: {e}")
            return []
    
    def _parse_page(self, html: str) -> List[ScrapedGroup]:
        """تحليل HTML الصفحة"""
        soup = BeautifulSoup(html, 'lxml')
        groups = []
        
        # البحث عن بطاقات المجموعات
        cards = soup.find_all('div', class_='card-body') or soup.find_all('div', class_='channel-card')
        
        for card in cards:
            try:
                group = self._parse_card(card)
                if group:
                    groups.append(group)
            except Exception as e:
                self.logger.debug(f"⚠️ Error parsing card: {e}")
                continue
        
        return groups
    
    def _parse_card(self, card) -> Optional[ScrapedGroup]:
        """تحليل بطاقة واحدة"""
        # استخراج الرابط
        link_elem = card.find('a', href=True)
        if not link_elem:
            return None
        
        href = link_elem['href']
        if not href.startswith('/'):
            href = '/' + href
        
        # استخراج اسم المستخدم
        username = None
        invite_link = None
        tgstat_url = urljoin(BASE_URL, href)
        
        if 't.me/' in href or 'telegram.me/' in href:
            parsed = urlparse(href)
            username = parsed.path.strip('/').split('/')[-1]
            invite_link = f"https://t.me/{username}"
        
        # استخراج العنوان
        title_elem = card.find('h3') or card.find('h4') or card.find('div', class_='title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # استخراج الوصف
        desc_elem = card.find('p') or card.find('div', class_='description')
        description = desc_elem.get_text(strip=True) if desc_elem else None
        
        # استخراج عدد الأعضاء
        members_elem = card.find('span', class_='members') or card.find('div', class_='subscribers')
        member_count = None
        if members_elem:
            text = members_elem.get_text(strip=True)
            member_count = self.parse_member_count(text)
        
        return ScrapedGroup(
            title=title,
            username=username,
            invite_link=invite_link,
            description=description,
            member_count=member_count,
            source_url=tgstat_url,
            source_name='tgstat'
        )


# اختبار
async def test():
    scraper = TGStatScraper()
    
    results = await scraper.scrape(
        max_results=10,
        country_code='SA'
    )
    
    print(f"Found {len(results)} groups")
    for group in results[:3]:
        print(f"- {group.title} (@{group.username})")


if __name__ == '__main__':
    asyncio.run(test())
