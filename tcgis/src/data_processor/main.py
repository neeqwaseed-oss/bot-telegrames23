"""
TCGIS - Data Processor
Enrich, classify, and validate scraped groups
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from shared.clients.postgres_client import get_db_session
from shared.clients.redis_client import redis_client
from shared.clients.elasticsearch_client import es_client
from shared.models.database_models import Group, Country, Category

from data_processor.processors.enrichment_processor import EnrichmentProcessor
from data_processor.processors.classification_processor import ClassificationProcessor
from data_processor.processors.deduplication_processor import DeduplicationProcessor
from data_processor.ml_models.language_detector import LanguageDetector


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """معالج البيانات الرئيسي"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.enrichment_processor = EnrichmentProcessor()
        self.classification_processor = ClassificationProcessor()
        self.deduplication_processor = DeduplicationProcessor()
    
    async def process_pending_groups(self, batch_size: int = 100):
        """
        معالجة المجموعات المعلقة
        
        Args:
            batch_size: عدد المجموعات في كل دفعة
        """
        from sqlalchemy import select
        
        async with get_db_session() as session:
            # جلب المجموعات المعلقة
            result = await session.execute(
                select(Group).where(Group.status == 'pending').limit(batch_size)
            )
            pending_groups = result.scalars().all()
            
            if not pending_groups:
                logger.info("ℹ️ No pending groups to process")
                return
            
            logger.info(f"🔄 Processing {len(pending_groups)} pending groups...")
            
            for group in pending_groups:
                try:
                    await self._process_group(group, session)
                except Exception as e:
                    logger.error(f"❌ Error processing group {group.id}: {e}")
                    group.status = 'error'
            
            await session.commit()
            logger.info(f"✅ Processed {len(pending_groups)} groups")
    
    async def _process_group(self, group: Group, session):
        """معالجة مجموعة واحدة"""
        # 1. كشف اللغة
        language, confidence = self.language_detector.detect(
            f"{group.title or ''} {group.description or ''}"
        )
        group.language_detected = language
        group.language_confidence = confidence
        
        # 2. تصنيف الدولة والفئة
        country, category = await self.classification_processor.classify(group, session)
        if country:
            group.country_id = country.id
        if category:
            group.category_id = category.id
        
        # 3. إثراء البيانات
        group = await self.enrichment_processor.enrich_group(group, session)
        
        # 4. حساب درجات الجودة
        group.quality_score = self._calculate_quality_score(group)
        group.activity_score = self._estimate_activity_score(group)
        
        # 5. التحقق من السبام
        group.spam_score = self._detect_spam(group)
        
        # 6. تحديث الحالة
        group.status = 'active' if group.spam_score < 50 else 'suspended'
        group.last_verified_at = datetime.utcnow()
        group.verification_count += 1
        group.verification_method = 'auto_ml'
        
        # 7. فهرسة في Elasticsearch
        await self._index_group(group, session)
        
        logger.info(f"✅ Processed group: {group.title} (ID: {group.id})")
    
    def _calculate_quality_score(self, group: Group) -> int:
        """حساب درجة الجودة"""
        score = 50  # البداية
        
        # العنوان
        if group.title:
            if len(group.title) >= 10:
                score += 10
            if len(group.title) <= 100:
                score += 5
        
        # الوصف
        if group.description:
            if len(group.description) >= 50:
                score += 10
            if len(group.description) >= 200:
                score += 5
        
        # عدد الأعضاء
        if group.member_count:
            if group.member_count >= 100:
                score += 10
            if group.member_count >= 1000:
                score += 10
            if group.member_count >= 10000:
                score += 5
        
        # التحقق
        if group.is_verified:
            score += 10
        
        # اللغة المكتشفة
        if group.language_detected and group.language_detected != 'unknown':
            score += 5
        
        return min(score, 100)
    
    def _estimate_activity_score(self, group: Group) -> int:
        """تقدير درجة النشاط"""
        score = 50
        
        if group.member_count:
            if group.member_count >= 1000:
                score += 20
            elif group.member_count >= 100:
                score += 10
        
        if group.message_frequency:
            if group.message_frequency >= 10:
                score += 20
            elif group.message_frequency >= 1:
                score += 10
        
        return min(score, 100)
    
    def _detect_spam(self, group: Group) -> int:
        """كشف السبام"""
        score = 0
        
        text = f"{group.title or ''} {group.description or ''}".lower()
        
        # كلمات سبام شائعة
        spam_keywords = [
            'free money', 'earn fast', 'get rich', 'click here',
            'limited time', 'act now', '100% guaranteed',
            'free', 'ربح سريع', 'فلوس', 'مجاني', 'مضمون',
            'احصل الآن', 'فرصة ذهبية', 'لا تفوت', 'سارع'
        ]
        
        for keyword in spam_keywords:
            if keyword in text:
                score += 15
        
        # عنوان طويل جداً
        if group.title and len(group.title) > 200:
            score += 10
        
        # وصف قصير جداً مع عدم وجود معلومات
        if not group.description or len(group.description) < 20:
            score += 5
        
        # رابط دعوة غير طبيعي
        if group.invite_link and len(group.invite_link) > 100:
            score += 5
        
        return min(score, 100)
    
    async def _index_group(self, group: Group, session):
        """فهرسة المجموعة في Elasticsearch"""
        try:
            # الحصول على أسماء الدولة والفئة
            country_name = None
            category_name = None
            
            if group.country_id:
                country_result = await session.execute(
                    select(Country).where(Country.id == group.country_id)
                )
                country = country_result.scalar_one_or_none()
                country_name = country.name_en if country else None
            
            if group.category_id:
                cat_result = await session.execute(
                    select(Category).where(Category.id == group.category_id)
                )
                category = cat_result.scalar_one_or_none()
                category_name = category.name_en if category else None
            
            doc = {
                'id': group.id,
                'telegram_id': group.telegram_id,
                'username': group.username,
                'title': group.title,
                'title_ar': group.title_ar,
                'description': group.description,
                'description_ar': group.description_ar,
                'country_code': country_name,
                'country_name': country_name,
                'category': category_name,
                'language': group.language_detected,
                'member_count': group.member_count,
                'quality_score': group.quality_score,
                'activity_score': group.activity_score,
                'status': group.status,
                'is_verified': group.is_verified,
                'is_featured': group.is_featured,
                'keywords': group.keywords or [],
                'tags': group.tags or [],
                'discovered_at': group.discovered_at.isoformat() if group.discovered_at else None,
                'last_activity_at': group.last_activity_at.isoformat() if group.last_activity_at else None
            }
            
            await es_client.index_group(doc)
            
        except Exception as e:
            logger.error(f"❌ Error indexing group {group.id}: {e}")


async def main():
    """الدالة الرئيسية"""
    processor = DataProcessor()
    
    # معالجة المجموعات المعلقة بشكل مستمر
    while True:
        try:
            await processor.process_pending_groups(batch_size=100)
            
            # انتظار قبل الدفعة التالية
            await asyncio.sleep(60)  # كل دقيقة
            
        except Exception as e:
            logger.error(f"❌ Processor error: {e}")
            await asyncio.sleep(300)  # انتظار 5 دقائق عند الخطأ


if __name__ == '__main__':
    asyncio.run(main())
