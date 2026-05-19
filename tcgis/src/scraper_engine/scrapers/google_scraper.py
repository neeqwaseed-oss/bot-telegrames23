"""
TCGIS - Google Scraper
Scrape Telegram groups from Google search results
"""

import asyncio
import logging
import urllib.parse
from typing import List, Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from scraper_engine.scrapers.base_scraper import BaseScraper, ScrapedGroup


logger = logging.getLogger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"


class GoogleScraper(BaseScraper):
    """جامع Google للبحث عن مجموعات Telegram"""
    
    def __init__(self):
        super().__init__("google")
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
        جلب مجموعات Telegram من نتائج Google
        """
        await self._init_session()
        results = []
        
        # كلمات البحث المختلفة للمجموعات العربية
        search_queries = self._build_search_queries(country_code, category)
        
        try:
            for search_query in search_queries:
                if len(results) >= max_results:
                    break
                
                self.logger.info(f"🔍 Searching Google: {search_query}")
                
                page_results = await self._search_google(
                    search_query,
                    max_results=max_results - len(results)
                )
                
                results.extend(page_results)
                self.logger.info(f"✅ Google query '{search_query}': Found {len(page_results)} groups")
                
                # تأخير بين الطلبات
                await asyncio.sleep(3)
            
            return self.deduplicate_results(results)[:max_results]
            
        except Exception as e:
            self.logger.error(f"❌ Google scraping error: {e}")
            return results
        
        finally:
            await self._close_session()
    
    async def test_connection(self) -> bool:
        """اختبار الاتصال"""
        try:
            await self._init_session()
            async with self.session.get(
                "https://www.google.com",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception:
            return False
    
    def _build_search_queries(self, country_code: Optional[str], category: Optional[str]) -> List[str]:
        """بناء استعلامات البحث"""
        queries = []
        
        country_names = {
            'SA': 'السعودية', 'AE': 'الإمارات', 'EG': 'مصر',
            'KW': 'الكويت', 'QA': 'قطر', 'BH': 'البحرين',
            'OM': 'عمان', 'JO': 'الأردن', 'LB': 'لبنان',
            'IQ': 'العراق', 'DZ': 'الجزائر', 'MA': 'المغرب',
            'TN': 'تونس', 'LY': 'ليبيا', 'SD': 'السودان',
            'YE': 'اليمن', 'SY': 'سوريا', 'PS': 'فلسطين',
        }
        
        country_name = country_names.get(country_code, '') if country_code else ''
        
        # استعلامات أساسية
        base_queries = [
            f"site:t.me/joinchat {country_name} group",
            f"site:t.me {country_name} مجموعة",
            f"site:t.me {country_name} قروب",
        ]
        
        if category:
            base_queries.extend([
                f"site:t.me {country_name} {category} مجموعة",
                f"site:t.me {country_name} {category} group",
            ])
        
        # إذا لم يتم تحديد دولة، نبحث بشكل عام
        if not country_name:
            base_queries = [
                "site:t.me/joinchat مجموعات عربية",
                "site:t.me قروب عربي",
                "site:t.me telegram groups arabic",
            ]
        
        return base_queries
    
    async def _search_google(
        self,
        query: str,
        max_results: int = 50
    ) -> List[ScrapedGroup]:
        """البحث في Google"""
        results = []
        
        params = {
            'q': query,
            'num': min(100, max_results * 2),  # نطلب أكثر لأن البعض ليس مجموعات
        }
        
        try:
            async with self.session.get(
                GOOGLE_SEARCH_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    self.logger.warning(f"⚠️ Google returned status {response.status}")
                    return []
                
                html = await response.text()
                return self._parse_results(html)[:max_results]
                
        except Exception as e:
            self.logger.error(f"❌ Error searching Google: {e}")
            return []
    
    def _parse_results(self, html: str) -> List[ScrapedGroup]:
        """تحليل نتائج Google"""
        soup = BeautifulSoup(html, 'lxml')
        groups = []
        
        # البحث عن روابط
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # التحقق من أن الرابط هو مجموعة Telegram
            if 't.me/' in href or 'telegram.me/' in href:
                try:
                    group = self._extract_group_from_url(href, link)
                    if group:
                        groups.append(group)
                except Exception as e:
                    self.logger.debug(f"⚠️ Error extracting group from URL: {e}")
                    continue
        
        return groups
    
    def _extract_group_from_url(self, url: str, element) -> Optional[ScrapedGroup]:
        """استخراج معلومات المجموعة من الرابط"""
        username = self.extract_username(url)
        
        if not username:
            return None
        
        invite_link = f"https://t.me/{username}" if not url.startswith('http') else url
        
        # محاولة استخراج العنوان من النص المحيط
        title = username
        parent = element.find_parent('div')
        if parent:
            title_elem = parent.find('h3') or parent.find('div', {'role': 'heading'})
            if title_elem:
                title = title_elem.get_text(strip=True)
        
        return ScrapedGroup(
            title=title[:255],
            username=username,
            invite_link=invite_link,
            description=None,
            source_url=url,
            source_name='google'
        )
