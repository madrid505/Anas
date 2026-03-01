# handlers_logic.py
from aiogram import Router, F, types
from config import ALLOWED_GROUPS
from database import load_db, save_db
import random

logic_router = Router()

@logic_router.message(F.chat.id.in_(ALLOWED_GROUPS))
async def core_logic(message: types.Message):
    db = load_db()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    # 1. احتساب نقاط ملك التفاعل
    if chat_id not in db["stats"]: db["stats"][chat_id] = {}
    user_data = db["stats"][chat_id].get(user_id, {"points": 0, "name": message.from_user.full_name})
    user_data["points"] += 1
    db["stats"][chat_id][user_id] = user_data

    # 2. كشف تغيير الاسم
    old_name = db["history"].get(user_id)
    if old_name and old_name != message.from_user.full_name:
        await message.answer(f"🔔 تغيير اسم!\n👤 القديم: {old_name}\n👤 الجديد: {message.from_user.full_name}\n🆔 ID: {user_id}")
    db["history"][user_id] = message.from_user.full_name

    # 3. رد "بوت" الترحيبي
    if message.text and "بوت" in message.text:
        await message.reply("🌹 إدارة قروب مونوبولي ترحب بك.. (الرسالة الكاملة التي طلبتها) 🌹")

    # 4. نظام الأقفال (المسح)
    locks = db["locks"].get(chat_id, {})
    if (message.photo and locks.get("صور")) or (message.voice and locks.get("فويسات")):
        await message.delete()

    save_db(db)

@logic_router.message(F.text == "كشف")
async def cmd_detect(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    db = load_db()
    points = db["stats"].get(str(message.chat.id), {}).get(str(target.id), {}).get("points", 0)
    await message.reply(f"🔍 الاسم: {target.full_name}\n🆔 ID: {target.id}\n✉️ الرسائل: {points}\n🌍 الدولة: جاري التحديد...")
