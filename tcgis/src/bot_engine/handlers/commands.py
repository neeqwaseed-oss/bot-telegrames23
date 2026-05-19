"""
TCGIS - Bot Commands Handler
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.clients.elasticsearch_client import es_client
from shared.clients.redis_client import redis_client


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """أمر /start"""
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
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """أمر /help"""
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
    
    await message.answer(help_text, reply_markup=builder.as_markup())


@router.message(Command("search"))
async def cmd_search(message: Message):
    """أمر /search"""
    query = message.text.replace('/search', '').strip()
    
    if not query:
        await message.answer(
            "❌ <b>يرجى إدخال كلمة للبحث</b>\n\n"
            "مثال: <code>/search تسويق</code>"
        )
        return
    
    # البحث في Elasticsearch
    await message.answer("🔍 <b>جاري البحث...</b>")
    
    try:
        results = await es_client.search_groups(
            query=query,
            filters={},
            page=1,
            per_page=10
        )
        
        if not results['results']:
            await message.answer(
                "😔 <b>لم يتم العثور على نتائج</b>\n\n"
                "جرب كلمات مختلفة أو تصفح حسب الدولة: <code>/country SA</code>"
            )
            return
        
        # بناء الرد
        response = f"🔍 <b>نتائج البحث عن:</b> <code>{query}</code>\n"
        response += f"📊 <b>إجمالي النتائج:</b> {results['total']}\n\n"
        
        for i, group in enumerate(results['results'], 1):
            flag = "✅" if group.get('is_verified') else ""
            members = group.get('member_count', 'غير معروف')
            
            response += (
                f"{i}. {flag} <b>{group['title']}</b>\n"
                f"   👥 الأعضاء: {members}\n"
                f"   🌐 الدولة: {group.get('country_name', 'غير محدد')}\n"
            )
            
            if group.get('username'):
                response += f"   🔗 @{group['username']}\n"
            elif group.get('invite_link'):
                response += f"   🔗 <a href='{group['invite_link']}'>رابط الانضمام</a>\n"
            
            response += "\n"
        
        # أزرار التنقل
        builder = InlineKeyboardBuilder()
        if results['total_pages'] > 1:
            builder.button(text="➡️ التالي", callback_data=f"search:{query}:2")
        builder.button(text="🔍 بحث جديد", callback_data="new_search")
        
        await message.answer(response, reply_markup=builder.as_markup())
        
    except Exception as e:
        await message.answer(
            f"❌ <b>حدث خطأ أثناء البحث</b>\n\n"
            f"الرجاء المحاولة لاحقاً"
        )


@router.message(Command("country"))
async def cmd_country(message: Message):
    """أمر /country"""
    country_code = message.text.replace('/country', '').strip().upper()
    
    if not country_code:
        await message.answer(
            "❌ <b>يرجى إدخال رمز الدولة</b>\n\n"
            "مثال: <code>/country SA</code> للسعودية\n"
            "استخدم <code>/help</code> لرؤية قائمة الدول"
        )
        return
    
    # البحث حسب الدولة
    await message.answer(f"🌐 <b>جاري جلب مجموعات الدولة...</b>")
    
    try:
        results = await es_client.search_groups(
            query="",
            filters={"country_code": country_code, "status": "active"},
            sort_by="members",
            page=1,
            per_page=15
        )
        
        if not results['results']:
            await message.answer(
                f"😔 <b>لم يتم العثور على مجموعات للدولة:</b> {country_code}\n\n"
                f"تأكد من صحة رمز الدولة أو جرب لاحقاً"
            )
            return
        
        # بناء الرد
        country_names = {
            'SA': '🇸🇦 السعودية',
            'AE': '🇦🇪 الإمارات',
            'EG': '🇪🇬 مصر',
            'KW': '🇰🇼 الكويت',
            'QA': '🇶🇦 قطر',
            'BH': '🇧🇭 البحرين',
            'OM': '🇴🇲 عمان',
            'JO': '🇯🇴 الأردن',
            'LB': '🇱🇧 لبنان',
            'IQ': '🇮🇶 العراق',
            'DZ': '🇩🇿 الجزائر',
            'MA': '🇲🇦 المغرب',
            'TN': '🇹🇳 تونس',
            'LY': '🇱🇾 ليبيا',
            'SD': '🇸🇩 السودان',
            'YE': '🇾🇪 اليمن',
            'SY': '🇸🇾 سوريا',
            'PS': '🇵🇸 فلسطين',
        }
        
        country_name = country_names.get(country_code, country_code)
        
        response = f"{country_name}\n"
        response += f"📊 <b>إجمالي المجموعات:</b> {results['total']}\n\n"
        
        for i, group in enumerate(results['results'], 1):
            members = group.get('member_count', 'غير معروف')
            quality = group.get('quality_score', 0)
            stars = "⭐" * (quality // 20) if quality else ""
            
            response += (
                f"{i}. <b>{group['title']}</b> {stars}\n"
                f"   👥 الأعضاء: {members}\n"
            )
            
            if group.get('description'):
                desc = group['description'][:100] + "..." if len(group['description']) > 100 else group['description']
                response += f"   📝 {desc}\n"
            
            if group.get('username'):
                response += f"   🔗 @{group['username']}\n"
            
            response += "\n"
        
        # أزرار التنقل والتصنيف
        builder = InlineKeyboardBuilder()
        
        # تصنيفات فرعية
        categories = results.get('aggregations', {}).get('by_category', {}).get('buckets', [])
        for cat in categories[:3]:
            builder.button(
                text=f"📁 {cat['key']}", 
                callback_data=f"country_cat:{country_code}:{cat['key']}:1"
            )
        
        if results['total_pages'] > 1:
            builder.button(text="➡️ المزيد", callback_data=f"country:{country_code}:2")
        
        builder.adjust(3)
        
        await message.answer(response, reply_markup=builder.as_markup())
        
    except Exception as e:
        await message.answer(
            f"❌ <b>حدث خطأ</b>\n\n"
            f"الرجاء المحاولة لاحقاً"
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """أمر /stats"""
    try:
        # إحصائيات Elasticsearch
        es_stats = await es_client.get_stats()
        
        # إحصائيات من الكاش
        total_countries = await redis_client.get('stats:total_countries') or "غير معروف"
        total_groups = es_stats.get('total_docs', 'غير معروف')
        
        stats_text = f"""
📊 <b>إحصائيات TCGIS</b>

📁 <b>المجموعات المُفهرسة:</b> {total_groups:,}
🌍 <b>الدول المدعومة:</b> {total_countries}
💾 <b>حجم الفهرس:</b> {es_stats.get('size_in_bytes', 0) / (1024*1024):.2f} MB

🔍 <b>البحثات اليوم:</b> {await redis_client.get('stats:daily_searches') or 0}
👥 <b>المستخدمين النشطين:</b> {await redis_client.get('stats:active_users') or 0}

📈 <b>المجموعات الجديدة اليوم:</b> {await redis_client.get('stats:new_today') or 0}
✅ <b>المجموعات المُحققة:</b> {await redis_client.get('stats:verified') or 0}

⚡ <b>حالة النظام:</b> 🟢 نشط
        """
        
        await message.answer(stats_text)
        
    except Exception as e:
        await message.answer(
            "📊 <b>إحصائيات TCGIS</b>\n\n"
            "⚡ <b>حالة النظام:</b> 🟢 نشط\n"
            "🔄 <b>الخدمات:</b> جميعها تعمل بشكل طبيعي"
        )


@router.message(Command("featured"))
async def cmd_featured(message: Message):
    """أمر /featured - المجموعات المميزة"""
    try:
        results = await es_client.search_groups(
            query="",
            filters={"is_featured": True, "status": "active"},
            sort_by="quality",
            page=1,
            per_page=10
        )
        
        if not results['results']:
            await message.answer(
                "⭐ <b>المجموعات المميزة</b>\n\n"
                "لا توجد مجموعات مميزة حالياً. تابعنا للتحديثات!"
            )
            return
        
        response = "⭐ <b>المجموعات المميزة</b>\n\n"
        
        for i, group in enumerate(results['results'], 1):
            members = group.get('member_count', 'غير معروف')
            quality = group.get('quality_score', 0)
            
            response += (
                f"{i}. 🏆 <b>{group['title']}</b>\n"
                f"   ⭐ الجودة: {quality}/100\n"
                f"   👥 الأعضاء: {members}\n"
                f"   🌐 {group.get('country_name', 'غير محدد')}\n"
            )
            
            if group.get('username'):
                response += f"   🔗 @{group['username']}\n"
            
            response += "\n"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer("❌ حدث خطأ أثناء جلب المجموعات المميزة")
