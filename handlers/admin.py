# handlers_admin.py
from aiogram import Router, F, types
from config import OWNER_ID
from database import load_db, save_db

admin_router = Router()

@admin_router.message(F.text.startswith(("رفع ", "تنزيل ")))
async def manage_ranks(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    if not message.reply_to_message: return await message.reply("👈 قم بالرد على العضو!")

    db = load_db()
    target_id = str(message.reply_to_message.from_user.id)
    rank = message.text.split(" ", 1)[1]
    
    if "رفع" in message.text:
        db["ranks"][target_id] = rank
        await message.reply(f"✅ تم رفع {message.reply_to_message.from_user.first_name} إلى {rank}")
    else:
        db["ranks"].pop(target_id, None)
        await message.reply(f"✅ تم تنزيله من رتبة {rank}")
    save_db(db)

@admin_router.message(F.text.in_({"حظر", "طرد", "كتم"}))
async def restrictions(message: types.Message):
    if not message.reply_to_message: return
    target_id = message.reply_to_message.from_user.id
    
    if target_id == OWNER_ID:
        return await message.reply("🚫 لا يمكنني لمس المالك الأساسي!")
    
    if message.text == "حظر":
        await message.chat.ban(target_id)
        await message.reply("✅ تم الحظر بنجاح.")
