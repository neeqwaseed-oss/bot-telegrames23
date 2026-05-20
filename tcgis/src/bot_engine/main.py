"""
TCGIS - Bot Engine
Telegram Bot using aiogram 3.x
"""

import os
import asyncio
import logging

# إعداد Event Loop بشكل استباقي لتفادي أخطاء pyrogram و uvloop على السيرفر
def setup_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

setup_event_loop()

from dotenv import load_dotenv

# تحميل ملف البيئة
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, InlineQuery
from aiogram.filters import Command, CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from shared.clients.postgres_client import init_db, close_db
from shared.clients.redis_client import redis_client
from shared.clients.elasticsearch_client import es_client

from bot_engine.handlers import commands, callbacks, messages
from bot_engine.config.settings import BOT_SETTINGS


# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# استيراد العميل العالمي
from shared.clients.telegram_search_client import tg_search_client

# إنشاء البوت والموزع
bot = Bot(
    token=os.getenv('BOT_TOKEN'), 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# تسجيل المعالجات
dp.include_router(commands.router)
dp.include_router(callbacks.router)
dp.include_router(messages.router)


async def on_startup():
    """الإعدادات عند بدء التشغيل"""
    try:
        await redis_client.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    try:
        await es_client.connect()
        logger.info("Elasticsearch connected")
    except Exception as e:
        logger.warning(f"Elasticsearch connection failed: {e}")

    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    # تهيئة عميل البحث العالمي
    try:
        await tg_search_client.connect()
    except Exception as e:
        logger.warning(f"Telegram Search Client initialization failed: {e}")
    
    # إعداد Webhook - فقط إذا لم نكن في وضع Polling
    env = os.getenv('ENV', 'development').lower()
    webhook_url = os.getenv('WEBHOOK_URL')
    logger.info(f"Checking mode: env={env}, webhook_url={webhook_url}")
    
    if env != 'development' and webhook_url and webhook_url.startswith('https'):
        await bot.set_webhook(
            url=f"{webhook_url}/webhook",
            secret_token=os.getenv('WEBHOOK_SECRET'),
            drop_pending_updates=True
        )
        logger.info(f"Webhook set: {webhook_url}/webhook")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted (using polling or invalid webhook configuration)")
    
    logger.info("Bot started successfully")


async def on_shutdown():
    """الإغلاق عند التوقف"""
    await close_db()
    await redis_client.disconnect()
    await es_client.disconnect()
    await tg_search_client.disconnect()
    await bot.session.close()
    logger.info("Bot stopped")


# Health check handler
async def handle_health_check(request: web.Request):
    """معالج فحص الحالة لبقاء السيرفر يعمل"""
    return web.Response(text="Bot is running!", status=200)


def generate_session():
    """توليد Session String للمرة الأولى"""
    from pyrogram import Client
    import asyncio
    
    async def main():
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        if not api_id or not api_hash:
            print("❌ API_ID or API_HASH missing!")
            return
            
        async with Client("temp_session", api_id=api_id, api_hash=api_hash) as app:
            session_string = await app.export_session_string()
            print("\n✅ Your TELEGRAM_SESSION string is:\n")
            print(f"TELEGRAM_SESSION={session_string}")
            print("\nCopy this string and add it to Render Environment Variables!\n")
            
    asyncio.run(main())


def main():
    """الدالة الرئيسية"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "session":
        generate_session()
        return

    env = os.getenv('ENV', 'development').lower()
    token = os.getenv('BOT_TOKEN')
    print(f"Starting bot in {env} mode...")
    print(f"Token present: {bool(token)}")
    
    if env == 'development':
        # تشغيل بال polling في التطوير
        asyncio.run(start_polling())
    else:
        # تشغيل بال webhook في الإنتاج
        start_webhook()


async def start_polling():
    """تشغيل بال Polling"""
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


def start_webhook():
    """تشغيل بال Webhook"""
    app = web.Application()
    
    # إضافة صفحة رئيسية لفحص الحالة (Health Check) وللـ Cron-job
    app.router.add_get('/', handle_health_check)
    
    # إعداد معالج طلبات التيليجرام
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.getenv('WEBHOOK_SECRET')
    )
    
    # تسجيل مسار الـ Webhook
    webhook_requests_handler.register(app, path="/webhook")
    
    # ربط الموزع بالتطبيق
    setup_application(app, dp, bot=bot)
    
    # إضافة وظائف بدء التشغيل والإغلاق
    app.on_startup.append(lambda _: on_startup())
    app.on_shutdown.append(lambda _: on_shutdown())
    
    # تشغيل السيرفر على البورت الذي يوفره Render (افتراضياً 10000 أو 8080)
    port = int(os.getenv('PORT', 8080))
    web.run_app(app, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
