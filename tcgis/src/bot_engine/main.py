"""
TCGIS - Bot Engine
Telegram Bot using aiogram 3.x
"""

import os
import asyncio
import logging
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
    await bot.session.close()
    logger.info("Bot stopped")


# Webhook handler
async def handle_webhook(request: web.Request):
    """معالج Webhook"""
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    expected = os.getenv('WEBHOOK_SECRET')
    
    if secret != expected:
        return web.Response(status=403, text="Forbidden")
    
    update = await request.json()
    await dp.feed_update(bot, update)
    return web.Response(status=200)


def main():
    """الدالة الرئيسية"""
    env = os.getenv('ENV', 'development')
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
    app.router.add_post('/webhook', handle_webhook)
    
    # إعداد webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=os.getenv('WEBHOOK_SECRET')
    )
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # إضافة hooks
    app.on_startup.append(lambda _: on_startup())
    app.on_shutdown.append(lambda _: on_shutdown())
    
    # تشغيل السيرفر
    port = int(os.getenv('BOT_PORT', 8080))
    web.run_app(app, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
