import json
from aiogram import types, F, Router
from config import ALLOWED_GROUPS

user_router = Router()

@user_router.message(F.chat.id.in_(ALLOWED_GROUPS))
async def tracking_system(message: types.Message):
    # نظام الردود عند مناداة البوت
    if message.text and "بوت" in message.text:
        await message.reply(
            "🌹 إدارة قروب مونوبولي ترحب بك 🌹\n"
            "نحن هنا لنجعلك سعيداً.. لا تلهك اللعبة عن ذكر الله.\n"
            "⛔ يمنع اللعب وقت الصلاة | يمنع التواصل مع المشرفات.\n"
            "👈 للتواصل: Anas أو Sakher"
        )

    # نظام الكشف (امر 'كشف')
    if message.text == "كشف":
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        await message.reply(
            f"🔍 **نظام الكشف**\n"
            f"👤 الاسم: {target.full_name}\n"
            f"🆔 ID: `{target.id}`\n"
            f"🌍 الدولة: (محددة برمجياً)"
        )
