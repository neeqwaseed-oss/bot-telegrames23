"""
TCGIS - Messages Handler
"""

import os
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.clients.elasticsearch_client import es_client
from shared.clients.telegram_search_client import tg_search_client

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message):
    """معالجة الرسائل النصية العامة كطلب بحث مباشر"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("⚠️ يرجى إدخال كلمة بحث أطول (حرفين على الأقل).")
        return

    msg = await message.answer(f"🔍 <b>جاري البحث عن:</b> <code>{query}</code>...")
    
    try:
        # محاولة البحث العالمي في تيليجرام أولاً
        results = await tg_search_client.search_global(query)
        
        if results:
            response_text = f"✅ <b>نتائج البحث لـ:</b> <code>{query}</code>\n\n"
            for i, res in enumerate(results, 1):
                response_text += f"{i}. <b>{res['title']}</b>\n"
                response_text += f"   🔗 t.me/{res['username']}\n\n" if res['username'] else "   🔗 رابط خاص\n\n"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="🏠 القائمة الرئيسية", callback_data="menu:main")
            await msg.edit_text(response_text, reply_markup=builder.as_markup(), disable_web_page_preview=True)
            return

        # إذا لم توجد نتائج عالمية، نجرب البحث في Elasticsearch
        db_results = await es_client.search_groups(query=query, filters={}, page=1)
        
        if db_results and db_results.get('results'):
            # تنسيق نتائج قاعدة البيانات (يمكنك إضافة الكود الخاص بها هنا)
            await message.answer("تم العثور على نتائج في قاعدة البيانات المحلية.")
            return

        # في حال عدم وجود أي نتائج
        env = os.getenv('ENV', 'production').lower()
        if env == 'development':
            await show_demo_results(message, query)
        else:
            await msg.edit_text("😔 لم يتم العثور على نتائج تطابق بحثك في سيرفرات تيليجرام.")

    except Exception as e:
        logger.error(f"Search error: {e}")
        await msg.edit_text("❌ عذراً، حدث خطأ أثناء البحث. يرجى المحاولة لاحقاً.")


async def show_demo_results(message: Message, query: str):
    """عرض نتائج تجريبية للتوضيح عند تعذر الاتصال بالخدمات"""
    demo_text = f"💡 <b>نتائج تجريبية لـ:</b> <code>{query}</code>\n"
    demo_text += "<i>(تظهر هذه النتائج لأن خدمات البحث متوقفة حالياً)</i>\n\n"
    
    demo_groups = [
        {"title": f"مجموعة {query} الكبرى", "members": "15,200", "link": "https://t.me/example1"},
        {"title": f"ملتقى عشاق {query}", "members": "8,450", "link": "https://t.me/example2"},
        {"title": f"أخبار {query} العاجلة", "members": "22,100", "link": "https://t.me/example3"},
    ]
    
    for i, group in enumerate(demo_groups, 1):
        demo_text += f"{i}. <b>{group['title']}</b>\n"
        demo_text += f"   👥 الأعضاء: {group['members']}\n"
        demo_text += f"   🔗 <a href='{group['link']}'>رابط الانضمام</a>\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 القائمة الرئيسية", callback_data="menu:main")
    
    await message.answer(demo_text, reply_markup=builder.as_markup(), disable_web_page_preview=True)


async def format_and_send_results(message: Message, query: str, results: dict):
    # كود تنسيق النتائج الحقيقية
    pass
