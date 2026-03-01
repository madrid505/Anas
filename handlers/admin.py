from aiogram import types, F, Router
from config import OWNER_ID

admin_router = Router()

@admin_router.message(F.text.startswith(("رفع ", "تنزيل ")))
async def ranking_system(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("⚠️ هذا الأمر للمالك الأساسي فقط.")
    
    if not message.reply_to_message:
        return await message.reply("⚠️ يجب الرد على العضو المراد تغيير رتبته.")
    
    target = message.reply_to_message.from_user
    rank = message.text.split(" ", 1)[1]
    
    # هنا يتم التخزين (سيتم ربطها بـ database.json في الملف الرئيسي)
    action = "رفع" if "رفع" in message.text else "تنزيل"
    await message.reply(f"✅ تم {action} العضو {target.full_name} إلى رتبة: {rank}")

@admin_router.message(F.text.in_({"حظر", "طرد", "كتم"}))
async def protection_actions(message: types.Message):
    if not message.reply_to_message: return
    
    target_id = message.reply_to_message.from_user.id
    if target_id == OWNER_ID:
        return await message.reply("🚫 لا يمكنني لمس المالك الأساسي، لديه حصانة!")

    if message.text == "حظر":
        await message.chat.ban(target_id)
        await message.reply(f"✅ تم حظر العضو بنجاح.")
