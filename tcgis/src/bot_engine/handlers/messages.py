"""
TCGIS - Messages Handler
"""

import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.clients.elasticsearch_client import es_client


router = Router()


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message):
    """معالجة الرسائل النصية العامة كطلب بحث مباشر"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("⚠️ يرجى إدخال كلمة بحث أطول (حرفين على الأقل).")
        return

    await message.answer(f"🔍 <b>جاري البحث عن:</b> <code>{query}</code>...")
    
    try:
        results = await es_client.search_groups(
            query=query,
            filters={},
            page=1,
            per_page=10
        )
        
        if not results['results']:
            # في التطوير نعرض بيانات تجريبية، في الإنتاج نعرض رسالة لا توجد نتائج
            env = os.getenv('ENV', 'production').lower()
            if env == 'development':
                await show_demo_results(message, query)
            else:
                await message.answer("😔 لم يتم العثور على نتائج تطابق بحثك.")
            return

        # تنسيق النتائج (نفس الكود الموجود في callbacks/commands)
        await format_and_send_results(message, query, results)

    except Exception:
        # في حالة فشل الاتصال بـ Elasticsearch، نعرض نتائج تجريبية فقط في التطوير
        env = os.getenv('ENV', 'production').lower()
        if env == 'development':
            await show_demo_results(message, query)
        else:
            await message.answer("❌ عذراً، حدث خطأ أثناء الاتصال بخدمة البحث. يرجى المحاولة لاحقاً.")


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
