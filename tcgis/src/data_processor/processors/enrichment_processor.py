"""
TCGIS - Enrichment Processor
Enrich group data with additional information
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from shared.models.database_models import Group, Country, Category


logger = logging.getLogger(__name__)


class EnrichmentProcessor:
    """معالج الإثراء لتحسين بيانات المجموعات"""
    
    @staticmethod
    async def enrich_group(group: Group, session) -> Group:
        """إثراء بيانات مجموعة"""
        logger.debug(f"🔄 Enriching group: {group.id}")
        
        # إثراء البيانات المفقودة
        if not group.title_ar and group.title:
            # يمكن إضافة ترجمة هنا
            pass
        
        if not group.description_ar and group.description:
            # يمكن إضافة ترجمة هنا
            pass
        
        # إنشاء SEO metadata
        if not group.seo_title and group.title:
            group.seo_title = f"{group.title} - Telegram Group"
        
        if not group.seo_description and group.description:
            desc = group.description[:150] + "..." if len(group.description) > 150 else group.description
            group.seo_description = desc
        
        # استخراج الكلمات المفتاحية
        if not group.keywords and group.title:
            keywords = EnrichmentProcessor._extract_keywords(group.title)
            group.keywords = keywords
        
        if not group.tags and group.description:
            tags = EnrichmentProcessor._extract_tags(group.description)
            group.tags = tags
        
        return group
    
    @staticmethod
    def _extract_keywords(text: str) -> list:
        """استخراج كلمات مفتاحية من النص"""
        # قائمة كلمات توقف عربية
        stop_words = {'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'الذي', 'التي', 'و', 'أو', 'مع', 'عن'}
        
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords[:20]  # أول 20 كلمة
    
    @staticmethod
    def _extract_tags(text: str) -> list:
        """استخراج وسوم من النص"""
        import re
        
        # البحث عن hashtags
        tags = re.findall(r'#(\w+)', text)
        
        # إذا لم توجد hashtags، نستخدم كلمات مفتاحية
        if not tags:
            words = text.lower().split()
            tags = [w for w in words if len(w) > 3][:10]
        
        return tags
