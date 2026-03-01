import re
from telethon import events
from database import db
from main import client, ALLOWED_GROUPS, OWNER_ID

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_locks_handler(event):
    # المدراء والمنشئ لا ينطبق عليهم القفل
    user_rank = db.get_rank(event.chat_id, event.sender_id)
    if user_rank in ["مدير", "مالك", "المنشئ"] or event.sender_id == OWNER_ID:
        return

    gid = str(event.chat_id)
    
    # قفل الروابط والمعرفات
    if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+|@\S+)', event.raw_text):
        await event.delete()

    # قفل الصور
    if event.photo and db.is_locked(gid, "photos"):
        await event.delete()
        
    # قفل التوجيه (Forward)
    if event.fwd_from and db.is_locked(gid, "forward"):
        await event.delete()
