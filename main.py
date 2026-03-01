import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

# استيراد الإعدادات والأنظمة المقسمة
try:
    from config import TOKEN, ALLOWED_GROUPS
    from handlers_logic import logic_router
    from handlers_admin import admin_router
except ImportError as e:
    print(f"❌ خطأ في استيراد الملفات المقسمة: {e}")
    exit(1)

# إعداد البوت والديسباتشر
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ربط الأقسام (الأنظمة المقسمة)
dp.include_router(admin_router)
dp.include_router(logic_router)

# --- نظام الأزرار (القائمة الرئيسية) ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏆 ملك التفاعل", callback_data="king_info"))
    builder.row(types.InlineKeyboardButton(text="🔍 نظام الكشف", callback_data="detect_info"))
    builder.row(types.InlineKeyboardButton(text="🔒 الأقفال", callback_data="locks_info"))
    builder.row(types.InlineKeyboardButton(text="🛡️ الإدارة", callback_data="admin_info"))
    builder.row(types.InlineKeyboardButton(text="🔄 عودة", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

# أمر "امر" لفتح القائمة
@dp.message(F.text == "امر")
async def show_menu(message: types.Message):
    if message.chat.id not in ALLOWED_GROUPS:
        return
    await message.answer("🛠️ **أهلاً بك في لوحة تحكم بوت مونوبولي:**\nاستخدم الأزرار أدناه للتحكم بالأنظمة.", reply_markup=get_main_menu())

# معالجة ضغطات الأزرار (التي كانت ناقصة)
@dp.callback_query()
async def process_callbacks(callback: CallbackQuery):
    if callback.data == "king_info":
        await callback.message.edit_text("👑 **نظام ملك التفاعل:**\nيتم احتساب النقاط تلقائياً لكل عضو يرسل رسالة في المجموعة.", reply_markup=get_main_menu())
    elif callback.data == "locks_info":
        await callback.message.edit_text("🔒 **نظام الأقفال:**\nيمكنك قفل الصور، الروابط، والفويسات عبر أوامر (قفل + النوع).", reply_markup=get_main_menu())
    elif callback.data == "main_menu":
        await callback.message.edit_text("🛠️ **القائمة الرئيسية:**", reply_markup=get_main_menu())
    await callback.answer()

# --- نظام النشر التلقائي (كل 15 دقيقة) ---
async def auto_broadcast():
    adhkar_list = [
        "سبحان الله وبحمده، سبحان الله العظيم",
        "لا إله إلا الله وحده لا شريك له",
        "اللهم صلِّ وسلم على نبينا محمد",
        "أستغفر الله العظيم وأتوب إليه",
        "لاحول ولا قوة إلا بالله العلي العظيم"
    ]
    while True:
        await asyncio.sleep(900)  # الانتظار 15 دقيقة
        for group_id in ALLOWED_GROUPS:
            try:
                msg = random.choice(adhkar_list)
                await bot.send_message(group_id, f"💡 **تذكير ديني:**\n\n{msg}")
            except Exception as e:
                logging.error(f"خطأ في النشر للمجموعة {group_id}: {e}")

# --- تشغيل البوت ---
async def start_process():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # تشغيل مهمة النشر في الخلفية
    asyncio.create_task(auto_broadcast())
    
    print("✅ تم ربط جميع الملفات (Logic + Admin + Config)")
    print("🚀 البوت يعمل الآن بنجاح على Northflank باسم main.py")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"فشل تشغيل البوت: {e}")

if __name__ == "__main__":
    asyncio.run(start_process())
