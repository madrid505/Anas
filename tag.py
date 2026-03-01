import asyncio
from telethon import events

tag_running = {}

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def tag_system(event):
    gid = event.chat_id
    msg = event.raw_text
    
    if msg == "تاك" or msg == "منشن":
        if not await check_privilege(event, "ادمن"): return
        
        tag_running[gid] = True
        participants = await client.get_participants(gid)
        users = [u for u in participants if not u.bot]
        
        await event.respond(f"📣 جاري بدء المنشن لـ {len(users)} عضو...")
        
        for i in range(0, len(users), 5):
            if not tag_running.get(gid): break
            batch = users[i:i+5]
            mentions = " ".join([f"[\u2063](tg://user?id={u.id})" for u in batch])
            await event.respond("📣 نداء للجميع " + mentions)
            await asyncio.sleep(2)
            
    elif msg == "وقف التاك" or msg == "ايقاف المنشن":
        tag_running[gid] = False
        await event.respond("🛑 تم إيقاف عملية المنشن")
