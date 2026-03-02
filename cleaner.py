import asyncio
from telethon import events
from database import db
# التعديل لمنع Circular Import وتعليق قاعدة البيانات
from __main__ import client, ALLOWED_GROUPS, check_privilege 

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def cleaner_handler(event):
    msg = event.raw_text
    chat_id = event.chat_id

    # التحقق من الصلاحية (يجب أن يكون مدير فأعلى لاستخدام التنظيف) لضمان الأمان
    if not await check_privilege(event, "مدير"):
        return

    # --- 1. مسح عدد معين من الرسائل (مثال: مسح 50) ---
    if msg.startswith("مسح ") and len(msg.split(" ")) > 1 and msg.split(" ")[1].isdigit():
        num = int(msg.split(" ")[1])
        if num > 100:
            await event.respond("⚠️ الحد الأقصى للمسح الملكي في المرة الواحدة هو 100 رسالة.")
            return

        # حذف رسالة الأمر المكتوبة أولاً لتنظيف الشات
        await event.delete()
        
        # جلب وحذف الرسائل المطلوبة من المجموعة
        messages = await client.get_messages(chat_id, limit=num)
        await client.delete_messages(chat_id, messages)
        
        # إرسال رسالة تأكيد مؤقتة ثم حذفها تلقائياً بعد 3 ثوانٍ لجمالية الدردشة
        confirm = await event.respond(f"🗑️ تم حذف **{len(messages)}** رسالة بنجاح.")
        await asyncio.sleep(3)
        await confirm.delete()

    # --- 2. مسح رسائل البوتات فقط (تنظيف شامل) ---
    elif msg == "تنظيف البوتات":
        await event.delete()
        # جلب آخر 100 رسالة وفلترة رسائل البوتات منها
        messages = await client.get_messages(chat_id, limit=100)
        bot_messages = [m for m in messages if m.sender and m.sender.bot]
        
        if bot_messages:
            await client.delete_messages(chat_id, bot_messages)
            confirm = await event.respond(f"🗑️ تم تنظيف **{len(bot_messages)}** رسالة من البوتات.")
            await asyncio.sleep(3)
            await confirm.delete()
        else:
            await event.respond("🔍 لم يتم العثور على رسائل بوتات مؤخراً في المجموعة.")

    # --- 3. مسح رسائل شخص معين (بالرد عليه) لإيقاف السبام ---
    elif msg == "مسح رسائله" and event.is_reply:
        await event.delete()
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        
        # البحث عن آخر رسائل لهذا المستخدم بالتحديد
        messages = await client.get_messages(chat_id, limit=100)
        user_messages = [m for m in messages if m.sender_id == user_id]
        
        if user_messages:
            await client.delete_messages(chat_id, user_messages)
            confirm = await event.respond(f"🗑️ تم حذف رسائل العضو المحددة بنجاح.")
            await asyncio.sleep(3)
            await confirm.delete()
        else:
            await event.respond("❌ لم يتم العثور على رسائل لهذا العضو حالياً.")
