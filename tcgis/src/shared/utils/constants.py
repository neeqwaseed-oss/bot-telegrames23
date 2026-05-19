"""
TCGIS - Constants
"""

# رموز الدول العربية
ARAB_COUNTRIES = {
    'SA': {'name_en': 'Saudi Arabia', 'name_ar': 'السعودية', 'flag': '🇸🇦'},
    'AE': {'name_en': 'United Arab Emirates', 'name_ar': 'الإمارات', 'flag': '🇦🇪'},
    'EG': {'name_en': 'Egypt', 'name_ar': 'مصر', 'flag': '🇪🇬'},
    'KW': {'name_en': 'Kuwait', 'name_ar': 'الكويت', 'flag': '🇰🇼'},
    'QA': {'name_en': 'Qatar', 'name_ar': 'قطر', 'flag': '🇶🇦'},
    'BH': {'name_en': 'Bahrain', 'name_ar': 'البحرين', 'flag': '🇧🇭'},
    'OM': {'name_en': 'Oman', 'name_ar': 'عمان', 'flag': '🇴🇲'},
    'JO': {'name_en': 'Jordan', 'name_ar': 'الأردن', 'flag': '🇯🇴'},
    'LB': {'name_en': 'Lebanon', 'name_ar': 'لبنان', 'flag': '🇱🇧'},
    'IQ': {'name_en': 'Iraq', 'name_ar': 'العراق', 'flag': '🇮🇶'},
    'DZ': {'name_en': 'Algeria', 'name_ar': 'الجزائر', 'flag': '🇩🇿'},
    'MA': {'name_en': 'Morocco', 'name_ar': 'المغرب', 'flag': '🇲🇦'},
    'TN': {'name_en': 'Tunisia', 'name_ar': 'تونس', 'flag': '🇹🇳'},
    'LY': {'name_en': 'Libya', 'name_ar': 'ليبيا', 'flag': '🇱🇾'},
    'SD': {'name_en': 'Sudan', 'name_ar': 'السودان', 'flag': '🇸🇩'},
    'YE': {'name_en': 'Yemen', 'name_ar': 'اليمن', 'flag': '🇾🇪'},
    'SY': {'name_en': 'Syria', 'name_ar': 'سوريا', 'flag': '🇸🇾'},
    'PS': {'name_en': 'Palestine', 'name_ar': 'فلسطين', 'flag': '🇵🇸'},
}

# الفئات الافتراضية
DEFAULT_CATEGORIES = [
    {'slug': 'general', 'name_en': 'General', 'name_ar': 'عام'},
    {'slug': 'technology', 'name_en': 'Technology', 'name_ar': 'تقنية'},
    {'slug': 'business', 'name_en': 'Business', 'name_ar': 'أعمال'},
    {'slug': 'education', 'name_en': 'Education', 'name_ar': 'تعليم'},
    {'slug': 'entertainment', 'name_en': 'Entertainment', 'name_ar': 'ترفيه'},
    {'slug': 'news', 'name_en': 'News', 'name_ar': 'أخبار'},
    {'slug': 'health', 'name_en': 'Health', 'name_ar': 'صحة'},
    {'slug': 'religion', 'name_en': 'Religion', 'name_ar': 'دين'},
    {'slug': 'travel', 'name_en': 'Travel', 'name_ar': 'سفر'},
    {'slug': 'food', 'name_en': 'Food', 'name_ar': 'طعام'},
    {'slug': 'fashion', 'name_en': 'Fashion', 'name_ar': 'موضة'},
    {'slug': 'automotive', 'name_en': 'Automotive', 'name_ar': 'سيارات'},
    {'slug': 'real-estate', 'name_en': 'Real Estate', 'name_ar': 'عقارات'},
    {'slug': 'jobs', 'name_en': 'Jobs', 'name_ar': 'وظائف'},
    {'slug': 'community', 'name_en': 'Community', 'name_ar': 'مجتمع'},
]

# حالات المجموعة
GROUP_STATUSES = ['active', 'inactive', 'banned', 'deleted', 'private', 'suspended', 'pending']

# أنواع المصادر
SOURCE_TYPES = ['directory', 'search_engine', 'social_media', 'api']

# مستويات الاشتراك
SUBSCRIPTION_TIERS = ['free', 'basic', 'premium', 'enterprise']
