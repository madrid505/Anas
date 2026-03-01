import json
import os
from aiogram import Router, F, types
from config import OWNER_ID, ALLOWED_GROUPS

admin_router = Router()

# ملف قاعدة البيانات المشترك
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {}, "ranks": {}, "locks": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stats": {}, "ranks": {}, "locks": {}}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- أوامر الرفع والتنزيل (حصرياً للمالك) ---
@admin_router.message(F.text.startswith(("رفع ", "تنزيل ")))
async def ranking_system(message: types.Message):
    # حماية المالك الأساسي
    if message.from_user.id != OWNER_ID:
        return # تجاهل إذا لم يكن المالك

    if not message.reply_to_message:
        return await message.reply("⚠️ يرجى الرد على رسالة الشخص الذي تريد رفعه أو تنزيله.")

    db = load_db()
    target_id = str(message.reply_to_message.from_user.id)
    target_name = message.reply_to_message.from_user.full_name
    
    # استخراج الرتبة من النص (مثلاً: رفع مدير)
    parts = message.text.split(" ", 1)
    rank_name = parts[1] if len(parts) > 1 else "عضو"

    if message.text.startswith("رفع"):
        db["ranks"][target_id] = rank_name
        await message.reply(f"✅ تم رفع **{target_name}** ليصبح: **{rank_name}**")
    else:
        if target_id in db["ranks"]:
            del db["ranks"][target_id]
            await message.reply(f"✅ تم تنزيل **{target_name}** من رتبة: **{rank_name}**")
        else:
            await message.reply("⚠️ هذا الشخص لا يملك رتبة أصلاً.")
    
    save_db(db)

# --- أوامر الطرد والحظر والكتم ---
@admin_router.message(F.text.in_({"حظر", "طرد", "كتم", "تقييد", "تنزيل الكل"}))
async def administrative_actions(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("⚠️ قم بالرد على الشخص لتنفيذ الإجراء.")

    target_id = message.reply_to_message.from_user.id
    
    # حماية المالك الأساسي (الحصانة المطلقة)
    if target_id == OWNER_ID:
        return await message.reply("🚫 لا يمكن تنفيذ هذا الإجراء على المالك الأساسي (حصانة مطلقة)!")

    # تنفيذ الإجراءات
    try:
        if message.text == "حظر":
            await message.chat.ban(target_id)
            await message.reply("✅ تم حظر العضو بنجاح.")
        elif message.text == "طرد":
            await message.chat.ban(target_id)
            await message.chat.unban(target_id)
            await message.reply("✅ تم طرد العضو.")
        elif message.text == "كتم":
            await message.chat.restrict(target_id, permissions=types.ChatPermissions(can_send_messages=False))
            await message.reply("✅ تم كتم العضو.")
        elif message.text == "تنزيل الكل":
            db = load_db()
            db["ranks"].pop(str(target_id), None)
            save_db(db)
            await message.reply("✅ تم تنزيل الشخص من جميع رتبه.")
    except Exception as e:
        await message.reply(f"❌ فشل الإجراء: تأكد أنني أملك صلاحيات أدمن.")

# --- كشف البوتات ---
@admin_router.message(F.text == "كشف البوتات")
async def detect_bots(message: types.Message):
    # سيقوم المشرف بطلب هذا الأمر لرؤية البوتات (يتطلب صلاحية الوصول للأعضاء)
    await message.reply("🔍 جاري فحص الأعضاء لكشف البوتات الدخيلة...")
