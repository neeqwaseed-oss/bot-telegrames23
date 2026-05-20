"""
TCGIS - Validators
Input validation utilities
"""

import re
from typing import Optional


def validate_telegram_username(username: str) -> bool:
    """التحقق من صحة اسم مستخدم Telegram"""
    if not username:
        return False
    # Telegram usernames: 5-32 chars, a-z, 0-9, underscores
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))


def validate_invite_link(link: str) -> bool:
    """التحقق من صحة رابط دعوة Telegram"""
    if not link:
        return False
    patterns = [
        r'^https?://t\.me/\+?[a-zA-Z0-9_-]+$',
        r'^https?://telegram\.me/\+?[a-zA-Z0-9_-]+$',
    ]
    return any(bool(re.match(p, link)) for p in patterns)


def validate_country_code(code: str) -> bool:
    """التحقق من صحة رمز الدولة"""
    if not code or len(code) != 2:
        return False
    from shared.utils.constants import ARAB_COUNTRIES
    return code.upper() in ARAB_COUNTRIES


def sanitize_query(query: str) -> str:
    """تنظيف استعلام البحث"""
    if not query:
        return ""
    # إزالة الأحرف الخاصة
    sanitized = re.sub(r'[<>{}/\\|;]', '', query)
    # تقطيع النص
    return sanitized.strip()[:200]


def parse_member_count(text: str) -> Optional[int]:
    """تحويل نص عدد الأعضاء إلى رقم"""
    if not text:
        return None
    
    text = text.lower().replace(',', '').replace(' ', '').replace('members', '').replace('subscribers', '')
    
    multipliers = {
        'k': 1000,
        'm': 1000000,
        'b': 1000000000
    }
    
    try:
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                number = float(text.replace(suffix, ''))
                return int(number * multiplier)
        
        return int(text)
    except ValueError:
        return None
