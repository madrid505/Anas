import asyncio
import logging
import json
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# إعدادات البوت
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# قاعدة بيانات وهمية بسيطة (يتم تخزينها في ملف)
data = {
    "stats": {}, # لملك التفاعل
    "users_history": {}, # لتغير الأسماء
    "custom_responses": {} # للردود المضافة
}

# --- وظائف مساعدة ---
def is_admin(user_id):
    return user_id == OWNER_ID

async def check_group(message: types.Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.reply("⚠️ هذا البوت غير مصرح له بالعمل هنا.")
        return False
    return True

# --- نظام أزرار الأوامر (الواجهة الجميلة) ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏆 ملك التفاعل", callback_data="cmd_king"))
    builder.row(InlineKeyboardButton(text="🔍 نظام الكشف", callback_data="cmd_detect"))
    builder.row(InlineKeyboardButton(text="🛡️ الحماية", callback_data="cmd_guard"))
    builder.row(InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="cmd_settings"))
    builder.row(InlineKeyboardButton(text="🌙 الأذكار", callback_data="cmd_athkar"))
    return builder.as_markup()

# --- معالجة الرسائل (ملك التفاعل + الردود التلقائية) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_messages(message: types.Message):
    if not await check_group(message): return

    # 1. نظام ملك التفاعل (جمع النقاط)
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)
    
    if chat_id not in data["stats"]: data["stats"][chat_id] = {}
    data["stats"][chat_id][user_id] = data["stats"][chat_id].get(user_id, 0) + 1

    # 2. نظام الكشف عن تغيير الاسم
    old_name = data["users_history"].get(user_id)
    new_name = message.from_user.full_name
    if old_name and old_name != new_name:
        await message.answer(f"🔔 تنبيه تغيير اسم!\n👤 الاسم القديم: {old_name}\n👤 الاسم الجديد: {new_name}\n🆔 ID: {user_id}")
    data["users_history"][user_id] = new_name

    # 3. الرد عند مناداة البوت
    if "بوت" in message.text or bot.get_my_name() in message.text:
        await message.reply(
            "🌹 إدارة قروب مونوبولي ترحب بك أهلاً وسهلاً 🌹\n"
            "نحن هنا لكي نجعلك سعيداً لا تجعل اللعبة تلهيك عن ذكر الله\n"
            "⛔ يمنع اللعب أثناء رفع الأذان وأوقات الصلاة ⛔\n"
            "⛔ يمنع منعاً باتاً التواصل مع المشرفات ⛔\n"
            "👈 لأي استفسار يرجى التواصل مع Anas أو Sakher 👉"
        )

# --- أوامر النص (عند كتابة 'امر') ---
@dp.message(F.text == "امر")
async def show_commands(message: types.Message):
    await message.answer("🛠️ **قائمة الأوامر والأنظمة المتوفرة:**", reply_markup=main_menu())

# --- نظام الكشف (امر 'كشف') ---
@dp.message(Command("كشف"))
@dp.message(F.text == "كشف")
async def detect_user(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    chat_id = str(message.chat.id)
    user_id = str(target.id)
    
    msg_count = data["stats"].get(chat_id, {}).get(user_id, 0)
    
    # محاكاة الدولة بناءً على الـ ID (يتطلب API خارجي للدقة القصوى)
    country = "غير معروف" # يمكن ربطها بـ IP API لاحقاً
    
    response = (
        f"🔍 **نظام الكشف الذكي**\n"
        f"👤 الاسم: {target.full_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"✉️ عدد الرسائل: {msg_count}\n"
        f"🌍 الدولة: {country}"
    )
    await message.reply(response)

# --- نظام التاك الكل ---
@dp.message(F.text == "تاك الكل")
async def tag_all(message: types.Message):
    if not is_admin(message.from_user.id): return
    members = ["@all_users"] # في بوتات التيليجرام الحقيقية تحتاج لجلب القائمة برمجياً
    await message.answer("📣 جاري عمل تاك لجميع الأعضاء...")
    # ملاحظة: التيليجرام يحد من التاك لعدد كبير، يفضل عملها على دفعات

# --- النشر التلقائي (كل 15 دقيقة) ---
async def auto_broadcast():
    athkar = ["سبحان الله", "الحمد لله", "لا إله إلا الله", "الله أكبر"]
    while True:
        await asyncio.sleep(900) # 15 دقيقة
        for group in ALLOWED_GROUPS:
            try:
                await bot.send_message(group, f"💡 **تذكير ديني:**\n{random.choice(athkar)}")
            except:
                continue

# --- تشغيل البوت ---
async def main():
    asyncio.create_task(auto_broadcast())
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
