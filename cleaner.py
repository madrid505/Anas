import asyncio
from telethon import events
from database import db
import main  # الوصول للعميل والصلاحيات

@main.client.on(events.NewMessage(chats=main.ALLOWED_GROUPS))
async def cleaner_handler(event):
    msg = event.raw_text
    chat_id = event.chat_id

    # التحقق من الصلاحية (يجب أن يكون مدير فأعلى لاستخدام التنظيف)
    if not await main.check_privilege(event, "مدير"):
        return

    # --- 1. مسح عدد معين من الرسائل (مثال: مسح 50) ---
    if msg.startswith("مسح ") and msg.split(" ")[1].isdigit():
        num = int(msg.split(" ")[1])
        if num > 100:
            await event.respond("⚠️ الحد الأقصى للمسح في المرة الواحدة هو 100 رسالة.")
            return

        # حذف رسالة الأمر أولاً
        await event.delete()
        
        # جلب وحذف الرسائل
        messages = await main.client.get_messages(chat_id, limit=num)
        await main.client.delete_messages(chat_id, messages)
        
        # إرسال تأكيد ثم حذفه تلقائياً بعد 3 ثوانٍ
        confirm = await event.respond(f"🗑️ تم حذف **{len(messages)}** رسالة بنجاح.")
        await asyncio.sleep(3)
        await confirm.delete()

    # --- 2. مسح رسائل البوتات فقط ---
    elif msg == "تنظيف البوتات":
        await event.delete()
        messages = await main.client.get_messages(chat_id, limit=100)
        bot_messages = [m for m in messages if m.sender and m.sender.bot]
        
        if bot_messages:
            await main.client.delete_messages(chat_id, bot_messages)
            confirm = await event.respond(f"🗑️ تم تنظيف **{len(bot_messages)}** رسالة من البوتات.")
            await asyncio.sleep(3)
            await confirm.delete()
        else:
            await event.respond("🔍 لم يتم العثور على رسائل بوتات مؤخراً.")

    # --- 3. مسح رسائل الشخص (بالرد عليه) ---
    elif msg == "مسح رسائله" and event.is_reply:
        await event.delete()
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        
        messages = await main.client.get_messages(chat_id, limit=100)
        user_messages = [m for m in messages if m.sender_id == user_id]
        
        if user_messages:
            await main.client.delete_messages(chat_id, user_messages)
            confirm = await event.respond(f"🗑️ تم حذف رسائل العضو المحددة.")
            await asyncio.sleep(3)
            await confirm.delete()
