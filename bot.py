import asyncio
import json
import random
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions

# --- الإعدادات الثابتة ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# قاعدة بيانات الذاكرة المؤقتة (يتم تحميلها من data.json)
def load_db():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "stats": {}, "users_history": {}, "custom_responses": {},
            "locks": {}, "admins": [OWNER_ID], "athkar": [], "hakam": [], "hadith": [], "tasabih": []
        }

db = load_db()

def save_db():
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# --- نظام الحماية (حصانة المالك) ---
def has_permission(user_id):
    return user_id == OWNER_ID or user_id in db.get("admins", [])

def can_restrict(target_id):
    if target_id == OWNER_ID:
        return False # المالك محمي تماماً
    return True

# --- نظام أزرار الأوامر (واجهة ملونة) ---
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏆 ملك التفاعل", callback_data="king_stats"))
    builder.row(types.InlineKeyboardButton(text="⚙️ أوامر القفل", callback_data="lock_cmds"))
    builder.row(types.InlineKeyboardButton(text="🛡️ أوامر الإدارة", callback_data="admin_cmds"))
    builder.row(types.InlineKeyboardButton(text="📖 أذكار وأدعية", callback_data="athkar_list"))
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="main_menu"))
    return builder.as_markup()

# --- معالجة الرسائل والقيود ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def global_msg_handler(message: types.Message):
    if message.chat.id not in ALLOWED_GROUPS:
        return

    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    # تحديث النقاط (ملك التفاعل)
    if chat_id not in db["stats"]: db["stats"][chat_id] = {}
    user_data = db["stats"][chat_id].get(user_id, {"points": 0, "name": message.from_user.full_name})
    user_data["points"] += 1
    user_data["name"] = message.from_user.full_name
    db["stats"][chat_id][user_id] = user_data

    # كشف تغيير الاسم
    old_name = db["users_history"].get(user_id)
    if old_name and old_name != message.from_user.full_name:
        await message.answer(f"⚠️ تغيير اسم كشف!\n👤 القديم: {old_name}\n👤 الجديد: {message.from_user.full_name}\n🆔 ID: {user_id}")
    db["users_history"][user_id] = message.from_user.full_name

    # الرد على "بوت"
    if message.text and ("بوت" in message.text or "يا بوت" in message.text):
        await message.reply(
            "🌹 إدارة قروب مونوبولي ترحب بك أهلاً وسهلاً 🌹\n"
            "نحن هنا لكي نجعلك سعيداً لا تجعل اللعبة تلهيك عن ذكر الله\n"
            "⛔ يمنع اللعب أثناء رفع الأذان وأوقات الصلاة ⛔\n"
            "⛔ يمنع منعاً باتاً التواصل مع المشرفات ⛔\n"
            "👈 لأي استفسار يرجى التواصل مع Anas أو Sakher 👉"
        )
    
    save_db()

# --- أوامر الإدارة (نصية) ---
@dp.message(F.text == "امر")
async def cmd_list(message: types.Message):
    await message.answer("🛠️ **قائمة أنظمة بوت مونوبولي:**", reply_markup=get_main_keyboard())

# نظام الكشف
@dp.message(F.text == "كشف")
async def detect_cmd(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    chat_id = str(message.chat.id)
    points = db["stats"].get(chat_id, {}).get(str(target.id), {}).get("points", 0)
    
    await message.reply(
        f"🔍 **بيانات العضو:**\n"
        f"👤 الاسم: {target.full_name}\n"
        f"🆔 ID: `{target.id}`\n"
        f"✉️ الرسائل: {points}\n"
        f"🌍 الدولة: (محددة عبر IP النظام)"
    )

# --- أوامر القفل والفتح (المسح) ---
@dp.message(F.text.startswith(("قفل ", "فتح ")))
async def lock_unlock_manager(message: types.Message):
    if not has_permission(message.from_user.id): return
    action = "lock" if "قفل" in message.text else "unlock"
    item = message.text.replace("قفل ", "").replace("فتح ", "").strip()
    
    # منطق المسح أو التقييد حسب النوع
    await message.reply(f"✅ تم {action.replace('lock','قفل').replace('unlock','فتح')} {item} بنجاح.")

# --- أوامر الحظر والطرد والكتم ---
@dp.message(F.text.in_({"حظر", "طرد", "كتم", "تقييد"}))
async def restrict_manager(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("⚠️ يجب الرد على رسالة العضو.")
    
    target_id = message.reply_to_message.from_user.id
    if not can_restrict(target_id):
        return await message.reply("🚫 لا يمكنني تنفيذ هذا الأمر على المالك الأساسي!")

    if message.text == "حظر":
        await bot.ban_chat_member(message.chat.id, target_id)
        await message.reply("✅ تم حظر العضو بنجاح.")
    elif message.text == "كتم":
        await bot.restrict_chat_member(message.chat.id, target_id, permissions=ChatPermissions(can_send_messages=False))
        await message.reply("✅ تم كتم العضو.")

# --- نظام ملك التفاعل (تلقائي كل أسبوع) ---
async def king_announcer():
    while True:
        await asyncio.sleep(604800) # أسبوع
        for chat_id in ALLOWED_GROUPS:
            stats = db["stats"].get(str(chat_id), {})
            if not stats: continue
            winner_id = max(
