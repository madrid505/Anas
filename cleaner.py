import asyncio
from telethon import events, types
from main import client, ALLOWED_GROUPS, OWNER_ID
from database import db

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def cleaner_system(event):
    msg = event.raw_text
    gid = event.chat_id
    
    # التحقق من الرتبة (مدير أو أعلى)
    user_rank = db.get_rank(str(gid), event.sender_id)
    if user_rank not in ["مدير", "مالك", "المنشئ"] and event.sender_id != OWNER_ID:
        return

    # --- 1. مسح الرسائل ---
    if msg.startswith("مسح "):
        num_str = msg.replace("مسح ", "")
        if num_str.isdigit():
            num = int(num_str)
            if num > 100: num = 100 # حد أقصى للحماية
            
            await event.delete() # حذف أمر المسح نفسه
            messages = await client.get_messages(gid, limit=num)
            await client.delete_messages(gid, messages)
            
            confirm = await event.respond(f"🧹 تم مسح **{len(messages)}** رسالة بنجاح.")
            await asyncio.sleep(3)
            await confirm.delete()

    # --- 2. تنظيف الحسابات المحذوفة ---
    elif msg == "تنظيف المحذوفين":
        del_users = 0
        async for user in client.iter_participants(gid):
            if user.deleted:
                try:
                    await client.kick_participant(gid, user.id)
                    del_users += 1
                except: continue
        await event.respond(f"✅ تم طرد **{del_users}** حساب محذوف من المجموعة.")

    # --- 3. مسح المحظورين (إلغاء حظر الكل) ---
    elif msg == "مسح المحظورين":
        await event.respond("⏳ جاري إلغاء حظر الجميع...")
        count = 0
        async for user in client.iter_participants(gid, filter=types.ChannelParticipantsKicked):
            try:
                await client.edit_permissions(gid, user.id, view_messages=True)
                count += 1
            except: continue
        await event.respond(f"🔓 تم مسح قائمة الحظر لـ **{count}** عضو.")

    # --- 4. مسح المكتومين (إلغاء كتم الكل) ---
    elif msg == "مسح المكتومين":
        count = 0
        async for user in client.iter_participants(gid, filter=types.ChannelParticipantsBanned):
            try:
                await client.edit_permissions(gid, user.id, send_messages=True)
                count += 1
            except: continue
        await event.respond(f"🔇 تم إلغاء الكتم عن **{count}** عضو بنجاح.")

    # --- 5. مسح رسائل البوت فقط ---
    elif msg == "مسح رسائلي":
        await event.delete()
        async for message in client.iter_messages(gid, from_user='me', limit=50):
            await message.delete()
