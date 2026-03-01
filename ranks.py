import re
from telethon import events
from database import db

# الرتب بالترتيب لسهولة التحقق
RANKS = ["عضو", "مميز", "ادمن", "مدير", "مالك", "المنشئ"]

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def ranking_system(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    if not event.is_reply: return
    reply = await event.get_reply_message()
    tid = str(reply.sender_id)
    
    # تحقق من رتبة الشخص الذي يرسل الأمر
    admin_rank = db.get_rank(gid, event.sender_id)
    if admin_rank not in ["مالك", "المنشئ"] and event.sender_id != OWNER_ID:
        return

    # أوامر الرفع (Regex الذكي)
    if re.match(r"^(رفع مالك|ارفع مالك)$", msg):
        db.set_rank(gid, tid, "مالك")
        await event.respond("👑 تم رفعه مالكاً في البوت")
        
    elif re.match(r"^(رفع مدير|ارفع مدير)$", msg):
        db.set_rank(gid, tid, "مدير")
        await event.respond("🎖️ تم رفعه مديراً في البوت")
        
    elif re.match(r"^(رفع ادمن|ارفع ادمن)$", msg):
        db.set_rank(gid, tid, "ادمن")
        await event.respond("🛡️ تم رفعه ادمن في البوت")
        
    elif re.match(r"^(رفع مميز|ارفع مميز)$", msg):
        db.set_rank(gid, tid, "مميز")
        await event.respond("✨ تم رفعه مميزاً في البوت")
        
    elif re.match(r"^(تنزيل|حذف رتبة)$", msg):
        db.set_rank(gid, tid, "عضو")
        await event.respond("👤 تم تنزيله لرتبة عضو")
