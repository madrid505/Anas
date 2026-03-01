import json
import random
import os
from aiogram import Router, F, types
from config import ALLOWED_GROUPS, OWNER_ID

logic_router = Router()

# --- إدارة قاعدة البيانات المصغرة ---
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {}, "names": {}, "locks": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- نظام معالجة الرسائل الشامل ---
@logic_router.message(F.chat.id.in_(ALLOWED_GROUPS))
async def global_handler(message: types.Message):
    db = load_db()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    user_name = message.from_user.full_name

    # 1. نظام ملك التفاعل (العد التراكمي)
    if chat_id not in db["stats"]: db["stats"][chat_id] = {}
    user_stats = db["stats"][chat_id].get(user_id, {"points": 0, "name": user_name})
    user_stats["points"] += 1
    user_stats["name"] = user_name
    db["stats"][chat_id][user_id] = user_stats

    # 2. نظام الكشف (تغير الاسم والـ ID)
    old_name = db["names"].get(user_id)
    if old_name and old_name != user_name:
        await message.answer(
            f"🔔 **تنبيه تغيير اسم!**\n\n"
            f"👤 الاسم القديم: {old_name}\n"
            f"👤 الاسم الجديد: {user_name}\n"
            f"🆔 ID: `{user_id}`"
        )
    db["names"][user_id] = user_name

    # 3. الرد التلقائي (بوت مونوبولي)
    if message.text and ("بوت" in message.text or "يا بوت" in message.text):
        await message.reply(
            "🌹 إدارة قروب مونوبولي ترحب بك أهلاً وسهلاً 🌹\n"
            "نحن هنا لكي نجعلك سعيداً لا تجعل اللعبة تلهيك عن ذكر الله\n\n"
            "⛔ يمنع اللعب أثناء رفع الأذان وأوقات الصلاة ⛔\n"
            "⛔ يمنع منعاً باتاً التواصل مع المشرفات ⛔\n\n"
            "👈 لأي استفسار يرجى التواصل مع Anas أو Sakher 👉"
        )

    # 4. نظام الأقفال (المسح التلقائي)
    locks = db["locks"].get(chat_id, {})
    # قفل الصور
    if message.photo and locks.get("صور"):
        await message.delete()
    # قفل الروابط
    if message.entities and any(e.type == 'url' for e in message.entities) and locks.get("روابط"):
        await message.delete()
    # قفل الفويسات
    if message.voice and locks.get("فويسات"):
        await message.delete()

    save_db(db)

# --- أمر الكشف (كشف) ---
@logic_router.message(F.text == "كشف")
async def cmd_kashf(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    db = load_db()
    points = db["stats"].get(str(message.chat.id), {}).get(str(target.id), {}).get("points", 0)
    
    # محاكاة الدولة (يمكن تطويرها بـ API)
    country = "الأردن 🇯🇴" if "Anas" in target.full_name else "جاري التحديد..."

    response = (
        f"🔍 **نظام الكشف الذكي**\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **الاسم:** {target.full_name}\n"
        f"🆔 **ID:** `{target.id}`\n"
        f"✉️ **الرسائل:** {points}\n"
        f"🌍 **الدولة:** {country}\n"
        f"━━━━━━━━━━━━━━"
    )
    await message.reply(response)

# --- أمر إعلان ملك التفاعل (يدوي أو أسبوعي) ---
@logic_router.message(F.text == "ملك التفاعل")
async def show_king(message: types.Message):
    db = load_db()
    chat_id = str(message.chat.id)
    if chat_id not in db["stats"] or not db["stats"][chat_id]:
        return await message.reply("❌ لا توجد بيانات تفاعل بعد.")
    
    # جلب الأعلى نقاطاً
    winner_id = max(db["stats"][chat_id], key=lambda x: db["
