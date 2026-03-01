import json
import random
import os
from aiogram import Router, F, types
from config import ALLOWED_GROUPS, OWNER_ID

logic_router = Router()

# --- إدارة قاعدة البيانات ---
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {}, "names": {}, "locks": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stats": {}, "names": {}, "locks": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- معالجة الرسائل ---
@logic_router.message(F.chat.id.in_(ALLOWED_GROUPS))
async def global_handler(message: types.Message):
    db = load_db()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    user_name = message.from_user.full_name

    # 1. ملك التفاعل
    if chat_id not in db["stats"]: 
        db["stats"][chat_id] = {}
    
    current_user_stat = db["stats"][chat_id].get(user_id, {"points": 0, "name": user_name})
    current_user_stat["points"] += 1
    current_user_stat["name"] = user_name
    db["stats"][chat_id][user_id] = current_user_stat

    # 2. كشف تغيير الاسم
    old_name = db["names"].get(user_id)
    if old_name and old_name != user_name:
        await message.answer(f"🔔 **تغيير اسم!**\n👤 القديم: {old_name}\n👤 الجديد: {user_name}\n🆔 ID: `{user_id}`")
    db["names"][user_id] = user_name

    # 3. ردود البوت
    if message.text and ("بوت" in message.text or "يا بوت" in message.text):
        await message.reply(
            "🌹 إدارة قروب مونوبولي ترحب بك أهلاً وسهلاً 🌹\n"
            "نحن هنا لكي نجعلك سعيداً لا تجعل اللعبة تلهيك عن ذكر الله\n\n"
            "⛔ يمنع اللعب أثناء رفع الأذان وأوقات الصلاة ⛔\n"
            "⛔ يمنع منعاً باتاً التواصل مع المشرفات ⛔\n\n"
            "👈 لأي استفسار يرجى التواصل مع Anas أو Sakher 👉"
        )

    # 4. الأقفال
    locks = db["locks"].get(chat_id, {})
    if message.photo and locks.get("صور"):
        await message.delete()
    if message.entities and any(e.type == 'url' for e in message.entities) and locks.get("روابط"):
        await message.delete()
    if message.voice and locks.get("فويسات"):
        await message.delete()

    save_db(db)

# --- أمر الكشف ---
@logic_router.message(F.text == "كشف")
async def cmd_kashf(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    db = load_db()
    points = db["stats"].get(str(message.chat.id), {}).get(str(target.id), {}).get("points", 0)
    
    response = (
        f"🔍 **نظام الكشف الذكي**\n"
        f"👤 **الاسم:** {target.full_name}\n"
        f"🆔 **ID:** `{target.id}`\n"
        f"✉️ **الرسائل:** {points}\n"
        f"🌍 **الدولة:** يتم التحديد..."
    )
    await message.reply(response)

# --- أمر ملك التفاعل (تم إصلاح الخطأ البرمجي هنا) ---
@logic_router.message(F.text == "ملك التفاعل")
async def show_king(message: types.Message):
    db = load_db()
    chat_id = str(message.chat.id)
    if chat_id not in db["stats"] or not db["stats"][chat_id]:
        return await message.reply("❌ لا توجد بيانات تفاعل بعد.")
    
    # إصلاح السطر الذي سبب الخطأ في Logs
    stats_dict = db["stats"][chat_id]
    winner_id = max(stats_dict, key=lambda x: stats_dict[x]['points'])
    winner = stats_dict[winner_id]
    
    text = (
        f"👑👑 ملك التفاعل 👑👑\n\n"
        f"👈👈 ({winner['name']}) 👉👉\n\n"
        f"🔥🔥 ({winner['points']} نقطة) 🔥🔥\n\n"
        f"⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
    )
    await message.reply(text)

# --- أوامر القفل والفتح ---
@logic_router.message(F.text.startswith(("قفل ", "فتح ")))
async def lock_manager(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    
    db = load_db()
    chat_id = str(message.chat.id)
    if chat_id not in db["locks"]: db["locks"][chat_id] = {}
    
    action = True if "قفل" in message.text else False
    item = message.text.replace("قفل ", "").replace("فتح ", "").strip()
    
    db["locks"][chat_id][item] = action
    save_db(db)
    
    status = "🔒 تم قفل" if action else "🔓 تم فتح"
    await message.reply(f"✅ {status} {item} بنجاح.")
