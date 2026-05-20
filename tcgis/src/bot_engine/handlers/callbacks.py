"""
TCGIS - Callbacks Handler
"""

import os
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.clients.elasticsearch_client import es_client


router = Router()


@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_callbacks(callback: CallbackQuery):
    """معالجة أزرار القائمة الرئيسية"""
    action = callback.data.split(":")[1]
    
    if action == "main":
        welcome_text = """
🌍 <b>مرحباً بك في TCGIS Bot!</b>

أنا بوت فهرسة المجموعات العامة في Telegram حسب الدولة.

<b>يمكنك استخدام الأزرار أدناه للتنقل في النظام:</b>
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 بحث عن مجموعات", callback_data="menu:search")
        builder.button(text="🌐 تصفح حسب الدولة", callback_data="menu:countries")
        builder.button(text="📊 إحصائيات النظام", callback_data="menu:stats")
        builder.button(text="ℹ️ المساعدة", callback_data="menu:help")
        builder.adjust(2)
        await callback.message.edit_text(welcome_text, reply_markup=builder.as_markup())
        
    elif action == "search":
        await callback.message.edit_text(
            "🔍 <b>خدمة البحث</b>\n\n"
            "من فضلك اكتب كلمة البحث مباشرة في الشات.\n"
            "مثال: <code>تسويق الرياض</code>",
            reply_markup=InlineKeyboardBuilder().button(text="🏠 عودة", callback_data="menu:main").as_markup()
        )
        
    elif action == "countries":
        countries_text = "🌐 <b>اختر الدولة لتصفح مجموعاتها:</b>"
        builder = InlineKeyboardBuilder()
        countries = [
            ('SA', '🇸🇦'), ('AE', '🇦🇪'), ('EG', '🇪🇬'), 
            ('KW', '🇰🇼'), ('QA', '🇶🇦'), ('BH', '🇧🇭'),
            ('OM', '🇴🇲'), ('JO', '🇯🇴'), ('LB', '🇱🇧'),
            ('IQ', '🇮🇶'), ('DZ', '🇩🇿'), ('MA', '🇲🇦')
        ]
        for code, flag in countries:
            builder.button(text=f"{flag} {code}", callback_data=f"country:{code}:1")
        builder.button(text="🏠 عودة للقائمة", callback_data="menu:main")
        builder.adjust(3)
        await callback.message.edit_text(countries_text, reply_markup=builder.as_markup())
        
    elif action == "stats":
        stats_text = """
📊 <b>إحصائيات النظام (تجريبي)</b>

👥 <b>إجمالي الأعضاء المكتشفين:</b> 1,240,500+
📁 <b>إجمالي المجموعات المؤرشفة:</b> 15,320
🌍 <b>الدول المغطاة:</b> 18 دولة عربية
✨ <b>مجموعات تم التحقق منها:</b> 4,200

<i>يتم تحديث البيانات تلقائياً كل 24 ساعة.</i>
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 عودة", callback_data="menu:main")
        await callback.message.edit_text(stats_text, reply_markup=builder.as_markup())
        
    elif action == "help":
        help_text = """
📖 <b>دليل الاستخدام</b>

<b>🔍 البحث:</b> استخدم زر البحث أو اكتب <code>/search</code>
<b>🌐 تصفح حسب الدولة:</b> اختر الدولة من القائمة
<b>📊 الإحصائيات:</b> عرض نمو المجموعات والأعضاء

يمكنك دائماً العودة للقائمة الرئيسية باستخدام <code>/start</code>
        """
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 ابدأ البحث", callback_data="menu:search")
        builder.button(text="🏠 القائمة الرئيسية", callback_data="menu:main")
        builder.adjust(1)
        await callback.message.edit_text(help_text, reply_markup=builder.as_markup())
    
    await callback.answer()


async def show_demo_country_results(callback: CallbackQuery, country_code: str):
    """عرض مجموعات تجريبية للدولة عند فشل الاتصال"""
    country_names = {
        'SA': '🇸🇦 السعودية', 'AE': '🇦🇪 الإمارات', 'EG': '🇪🇬 مصر',
        'KW': '🇰🇼 الكويت', 'QA': '🇶🇦 قطر', 'BH': '🇧🇭 البحرين',
        'OM': '🇴🇲 عمان', 'JO': '🇯🇴 الأردن', 'LB': '🇱🇧 لبنان',
        'IQ': '🇮🇶 العراق', 'DZ': '🇩🇿 الجزائر', 'MA': '🇲🇦 المغرب',
        'TN': '🇹نون تونس', 'LY': '🇱🇾 ليبيا', 'SD': '🇸🇩 السودان',
        'YE': '🇾🇪 اليمن', 'SY': '🇸🇾 سوريا', 'PS': '🇵🇸 فلسطين',
    }
    country_name = country_names.get(country_code, country_code)
    
    demo_text = f"🌐 <b>مجموعات {country_name}:</b>\n"
    demo_text += "<i>(تظهر هذه النتائج التجريبية لتعذر الاتصال بقاعدة البيانات حالياً)</i>\n\n"
    
    demo_groups = [
        {"title": f"تجمع {country_name} العقاري", "members": "4,200", "link": "https://t.me/example_re"},
        {"title": f"وظائف {country_name} الشاغرة", "members": "12,500", "link": "https://t.me/example_jobs"},
        {"title": f"منصة {country_name} التقنية", "members": "7,800", "link": "https://t.me/example_tech"},
    ]
    
    for i, group in enumerate(demo_groups, 1):
        demo_text += f"{i}. <b>{group['title']}</b>\n"
        demo_text += f"   👥 الأعضاء: {group['members']}\n"
        demo_text += f"   🔗 <a href='{group['link']}'>رابط الانضمام</a>\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 عودة للدول", callback_data="menu:countries")
    builder.button(text="🏠 القائمة الرئيسية", callback_data="menu:main")
    builder.adjust(1)
    
    await callback.message.edit_text(demo_text, reply_markup=builder.as_markup(), disable_web_page_preview=True)


@router.callback_query(F.data.startswith("search:"))
async def handle_search_pagination(callback: CallbackQuery):
    """تنقل نتائج البحث"""
    parts = callback.data.split(":")
    query = parts[1]
    page = int(parts[2])
    
    await callback.answer("⏳ جاري التحميل...")
    
    try:
        results = await es_client.search_groups(
            query=query,
            filters={},
            page=page,
            per_page=10
        )
        
        if not results['results']:
            await callback.message.edit_text("😔 لا توجد نتائج إضافية")
            return
        
        response = f"🔍 <b>نتائج البحث عن:</b> <code>{query}</code>\n"
        response += f"📊 <b>الصفحة:</b> {page}/{results['total_pages']}\n\n"
        
        for i, group in enumerate(results['results'], 1):
            num = (page - 1) * 10 + i
            response += (
                f"{num}. <b>{group['title']}</b>\n"
                f"   👥 {group.get('member_count', 'غير معروف')}\n"
                f"   🌐 {group.get('country_name', 'غير محدد')}\n\n"
            )
        
        # أزرار التنقل
        builder = InlineKeyboardBuilder()
        if page > 1:
            builder.button(text="⬅️ السابق", callback_data=f"search:{query}:{page-1}")
        if page < results['total_pages']:
            builder.button(text="➡️ التالي", callback_data=f"search:{query}:{page+1}")
        
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
        
    except Exception as e:
        await callback.answer("❌ حدث خطأ")


@router.callback_query(F.data.startswith("country:"))
async def handle_country_pagination(callback: CallbackQuery):
    """تنقل مجموعات الدولة"""
    parts = callback.data.split(":")
    country_code = parts[1]
    page = int(parts[2])
    
    await callback.answer("⏳ جاري التحميل...")
    
    try:
        results = await es_client.search_groups(
            query="",
            filters={"country_code": country_code, "status": "active"},
            sort_by="members",
            page=page,
            per_page=15
        )
        
        if not results['results']:
            # في التطوير نعرض بيانات تجريبية، في الإنتاج نعرض رسالة لا توجد نتائج
            env = os.getenv('ENV', 'production').lower()
            if env == 'development':
                await show_demo_country_results(callback, country_code)
            else:
                await callback.message.edit_text("😔 لا توجد مجموعات مؤرشفة لهذه الدولة حالياً.")
            return
        
        country_names = {
            'SA': '🇸🇦 السعودية', 'AE': '🇦🇪 الإمارات', 'EG': '🇪🇬 مصر',
            'KW': '🇰🇼 الكويت', 'QA': '🇶🇦 قطر', 'BH': '🇧🇭 البحرين',
            'OM': '🇴🇲 عمان', 'JO': '🇯🇴 الأردن', 'LB': '🇱🇧 لبنان',
            'IQ': '🇮🇶 العراق', 'DZ': '🇩🇿 الجزائر', 'MA': '🇲🇦 المغرب',
            'TN': '🇹🇳 تونس', 'LY': '🇱🇾 ليبيا', 'SD': '🇸🇩 السودان',
            'YE': '🇾🇪 اليمن', 'SY': '🇸🇾 سوريا', 'PS': '🇵🇸 فلسطين',
        }
        
        country_name = country_names.get(country_code, country_code)
        
        response = f"{country_name} - الصفحة {page}\n\n"
        
        for i, group in enumerate(results['results'], 1):
            num = (page - 1) * 15 + i
            response += (
                f"{num}. <b>{group['title']}</b>\n"
                f"   👥 {group.get('member_count', 'غير معروف')}\n"
            )
            if group.get('username'):
                response += f"   🔗 t.me/{group['username']}\n\n"
            else:
                response += f"   🔗 <a href='{group.get('invite_link', '#')}'>رابط الانضمام</a>\n\n"
        
        # أزرار التنقل
        builder = InlineKeyboardBuilder()
        if page > 1:
            builder.button(text="⬅️ السابق", callback_data=f"country:{country_code}:{page-1}")
        builder.button(text="➡️ التالي", callback_data=f"country:{country_code}:{page+1}")
        builder.button(text="🏠 القائمة الرئيسية", callback_data="menu:main")
        builder.adjust(2)
        
        await callback.message.edit_text(response, reply_markup=builder.as_markup())
        
    except Exception:
        env = os.getenv('ENV', 'production').lower()
        if env == 'development':
            await show_demo_country_results(callback, country_code)
        else:
            await callback.answer("❌ عذراً، تعذر الاتصال بخدمة البيانات حالياً.")


@router.callback_query(F.data == "new_search")
async def handle_new_search(callback: CallbackQuery):
    """بدء بحث جديد"""
    await callback.answer("🔍 أدخل كلمة البحث")
    await callback.message.answer("🔍 <b>أدخل كلمة البحث:</b>\n<code>/search [كلمة]</code>")
