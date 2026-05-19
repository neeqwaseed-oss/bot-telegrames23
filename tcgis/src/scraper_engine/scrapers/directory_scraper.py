"""
TCGIS - Directory Scraper
Scrape Telegram groups from group directories
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from scraper_engine.scrapers.base_scraper import BaseScraper, ScrapedGroup


logger = logging.getLogger(__name__)

# قائمة أدلة المجموعات
DIRECTORIES = [
    "https://telegram-directory.com",
    "https://tgstat.com",
    "https://combot.org/telegram/groups",
]


class DirectoryScraper(BaseScraper):
    """جامع أدلة المجموعات"""
    
    def __init__(self):
        super().__init__("directory")
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
        جمع المجموعات من أدلة المجموعات
        """
        await self._init_session()
        results = []
        
        try:
            for directory_url in DIRECTORIES:
                if len(results) >= max_results:
                    break
                
                self.logger.info(f"🔍 Scraping directory: {directory_url}")
                
                try:
                    page_results = await self._scrape_directory(
                        directory_url,
                        max_results=max_results - len(results),
                        country_code=country_code,
                        category=category
                    )
                    
                    results.extend(page_results)
                    self.logger.info(f"✅ Directory '{directory_url}': Found {len(page_results)} groups")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error scraping directory {directory_url}: {e}")
                    continue
                
                # تأخير بين الطلبات
                await asyncio.sleep(2)
            
            return self.deduplicate_results(results)[:max_results]
            
        except Exception as e:
            self.logger.error(f"❌ Directory scraping error: {e}")
            return results
        
        finally:
            await self._close_session()
    
    async def test_connection(self) -> bool:
        """اختبار الاتصال"""
        try:
            await self._init_session()
            async with self.session.get(
                DIRECTORIES[0],
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _scrape_directory(
        self,
        base_url: str,
        max_results: int = 100,
        country_code: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[ScrapedGroup]:
        """جمع من دليل واحد"""
        results = []
        
        try:
            async with self.session.get(
                base_url,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # البحث عن بطاقات المجموعات
                # كل دليل له هيكل مختلف، نحاول عدة استراتيجيات
                groups = self._parse_generic(soup, base_url)
                results.extend(groups)
                
                # البحث عن صفحات إضافية
                pagination_links = soup.find_all('a', href=True)
                page_urls = set()
                
                for link in pagination_links:
                    href = link['href']
                    if 'page' in href.lower() or 'p=' in href:
                        full_url = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                        page_urls.add(full_url)
                
                # جلب صفحة إضافية واحدة فقط لتجنب الحظر
                for page_url in list(page_urls)[:2]:
                    try:
                        async with self.session.get(
                            page_url,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as page_response:
                            if page_response.status == 200:
                                page_html = await page_response.text()
                                page_soup = BeautifulSoup(page_html, 'lxml')
                                page_groups = self._parse_generic(page_soup, base_url)
                                results.extend(page_groups)
                                await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.debug(f"⚠️ Error fetching page {page_url}: {e}")
                        continue
                
        except Exception as e:
            self.logger.error(f"❌ Error scraping directory {base_url}: {e}")
        
        return results[:max_results]
    
    def _parse_generic(self, soup: BeautifulSoup, base_url: str) -> List[ScrapedGroup]:
        """تحليل عام يعمل مع معظم الأدلة"""
        groups = []
        
        # البحث عن جميع الروابط التي تحتوي على t.me
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            if 't.me/' in href or 'telegram.me/' in href:
                try:
                    username = self.extract_username(href)
                    if not username or username in ['joinchat', 'addstickers', 'bot', '']:
                        continue
                    
                    # استخراج العنوان
                    title = link.get_text(strip=True) or username
                    
                    # محاولة إيجاد الوصف من العنصر الأب
                    description = None
                    parent = link.find_parent('div', class_=True)
                    if parent:
                        desc_elem = parent.find('p') or parent.find('div', class_='description')
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                    
                    group = ScrapedGroup(
                        title=title[:255],
                        username=username,
                        invite_link=f"https://t.me/{username}" if not href.startswith('http') else href,
                        description=description,
                        source_url=base_url,
                        source_name='directory'
                    )
                    
                    groups.append(group)
                    
                except Exception as e:
                    self.logger.debug(f"⚠️ Error parsing link {href}: {e}")
                    continue
        
        return groups
