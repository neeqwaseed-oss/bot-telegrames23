"""
TCGIS - Bot Engine Settings
"""

import os


BOT_SETTINGS = {
    "token": os.getenv("BOT_TOKEN"),
    "webhook_url": os.getenv("WEBHOOK_URL"),
    "webhook_secret": os.getenv("WEBHOOK_SECRET"),
    "parse_mode": "HTML",
    "default_language": "ar",
    "max_search_results": 10,
    "max_country_results": 15,
    "rate_limit_per_minute": 30,
}

# نصوص الرسائل
MESSAGES = {
    "ar": {
        "welcome": "مرحباً بك في TCGIS Bot!",
        "search_prompt": "أدخل كلمة البحث:",
        "no_results": "لم يتم العثور على نتائج",
        "error": "حدث خطأ، يرجى المحاولة لاحقاً",
    },
    "en": {
        "welcome": "Welcome to TCGIS Bot!",
        "search_prompt": "Enter search term:",
        "no_results": "No results found",
        "error": "An error occurred, please try again later",
    }
}
