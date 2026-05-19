"""
TCGIS - Classification Processor
Classify groups by country and category
"""

import logging
from typing import Optional, Tuple
from sqlalchemy import select

from shared.models.database_models import Group, Country, Category


logger = logging.getLogger(__name__)


class ClassificationProcessor:
    """معالج التصنيف للمجموعات"""
    
    # قاموس الكلمات المفتاحية للدول العربية
    COUNTRY_KEYWORDS = {
        'SA': ['السعودية', 'سعودي', 'الرياض', 'جدة', 'مكة', 'الدمام', 'ksa', 'saudi'],
        'AE': ['الإمارات', 'امارات', 'دبي', 'أبوظبي', 'الشارقة', 'uae', 'dubai'],
        'EG': ['مصر', 'مصري', 'القاهرة', 'الإسكندرية', 'egypt', 'cairo'],
        'KW': ['الكويت', 'كويتي', 'الكويتية', 'kuwait'],
        'QA': ['قطر', 'قطري', 'الدوحة', 'qatar', 'doha'],
        'BH': ['البحرين', 'بحريني', 'المنامة', 'bahrain'],
        'OM': ['عمان', 'عماني', 'مسقط', 'oman', 'muscat'],
        'JO': ['الأردن', 'أردني', 'عمان', 'jordan', 'amman'],
        'LB': ['لبنان', 'لبناني', 'بيروت', 'lebanon', 'beirut'],
        'IQ': ['العراق', 'عراقي', 'بغداد', 'iraq', 'baghdad'],
        'DZ': ['الجزائر', 'جزائري', 'الجزائرية', 'algeria'],
        'MA': ['المغرب', 'مغربي', 'الدار البيضاء', 'morocco', 'casablanca'],
        'TN': ['تونس', 'تونسي', 'tunisia'],
        'LY': ['ليبيا', 'ليبي', 'طرابلس', 'libya', 'tripoli'],
        'SD': ['السودان', 'سوداني', 'الخرطوم', 'sudan', 'khartoum'],
        'YE': ['اليمن', 'يمني', 'صنعاء', 'yemen', 'sanaa'],
        'SY': ['سوريا', 'سوري', 'دمشق', 'syria', 'damascus'],
        'PS': ['فلسطين', 'فلسطيني', 'غزة', 'palestine', 'gaza'],
    }
    
    # قاموس الكلمات المفتاحية للفئات
    CATEGORY_KEYWORDS = {
        'technology': ['تقنية', 'تكنولوجيا', 'برمجة', 'كمبيوتر', 'هاتف', 'tech', 'programming', 'coding', 'developer', 'software', 'app', 'android', 'ios', 'ai', 'blockchain', 'crypto'],
        'business': ['أعمال', 'تجارة', 'استثمار', 'تسويق', 'بيع', 'شراء', 'business', 'marketing', 'sales', 'investment', 'trading', 'forex', 'ecommerce'],
        'education': ['تعليم', 'دراسة', 'جامعة', 'مدرسة', 'كورس', 'تدريب', 'education', 'learning', 'course', 'university', 'school', 'tutorial'],
        'entertainment': ['ترفيه', 'أفلام', 'مسلسلات', 'ألعاب', 'موسيقى', 'entertainment', 'movies', 'series', 'games', 'gaming', 'music', 'fun'],
        'news': ['أخبار', 'إعلام', 'صحافة', 'news', 'media', 'journalism', 'breaking'],
        'health': ['صحة', 'طب', 'رياضة', 'لياقة', 'health', 'medical', 'fitness', 'gym', 'sport', 'doctor'],
        'religion': ['دين', 'إسلام', 'قرآن', 'حديث', 'religion', 'islam', 'quran', 'hadith', 'christian', 'bible'],
        'travel': ['سفر', 'سياحة', 'فنادق', 'travel', 'tourism', 'hotel', 'trip', 'vacation'],
        'food': ['طعام', 'أكل', 'مطاعم', 'وصفات', 'food', 'restaurant', 'recipe', 'cooking', 'chef'],
        'fashion': ['موضة', 'أزياء', 'جمال', 'fashion', 'style', 'beauty', 'makeup', 'clothes'],
        'automotive': ['سيارات', 'سيارة', 'موتور', 'cars', 'automotive', 'vehicle', 'motor'],
        'real-estate': ['عقار', 'عقارات', 'شقة', 'بيت', 'real estate', 'property', 'apartment', 'house', 'rent'],
        'jobs': ['وظائف', 'عمل', 'توظيف', 'jobs', 'career', 'hiring', 'employment', 'remote'],
        'community': ['مجتمع', 'نقاش', 'دردشة', 'community', 'chat', 'discussion', 'talk'],
    }
    
    @classmethod
    async def classify_country(cls, group: Group, session) -> Optional[Country]:
        """تصنيف الدولة"""
        text = f"{group.title or ''} {group.description or ''}".lower()
        
        # البحث عن تطابق
        for code, keywords in cls.COUNTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    result = await session.execute(
                        select(Country).where(Country.code == code)
                    )
                    country = result.scalar_one_or_none()
                    if country:
                        logger.debug(f"✅ Classified country: {code} for group {group.id}")
                        return country
        
        # إذا لم يتم العثور، حاول من اللغة
        if group.language_detected == 'arabic':
            # افتراضياً نتركها None
            pass
        
        return None
    
    @classmethod
    async def classify_category(cls, group: Group, session) -> Optional[Category]:
        """تصنيف الفئة"""
        text = f"{group.title or ''} {group.description or ''}".lower()
        
        # البحث عن أفضل تطابق
        best_match = None
        best_score = 0
        
        for slug, keywords in cls.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_score = score
                best_match = slug
        
        if best_match and best_score > 0:
            result = await session.execute(
                select(Category).where(Category.slug == best_match)
            )
            category = result.scalar_one_or_none()
            if category:
                logger.debug(f"✅ Classified category: {best_match} for group {group.id}")
                return category
        
        # فئة افتراضية
        result = await session.execute(
            select(Category).where(Category.slug == 'general')
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def classify(cls, group: Group, session) -> Tuple[Optional[Country], Optional[Category]]:
        """تصنيف المجموعة بالكامل"""
        country = await cls.classify_country(group, session)
        category = await cls.classify_category(group, session)
        
        return country, category
