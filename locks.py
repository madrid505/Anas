import re
from telethon import events
from database import db
from main import client, ALLOWED_GROUPS, OWNER_ID

# قائمة الميزات التي يدعمها البوت (نفس نظام تون)
FEATURES = {
    "الروابط": "links",
    "الصور": "photos",
    "الملصقات": "stickers",
    "المتحركة": "gifs",
    "التوجيه": "forward",
    "المعرفات": "usernames",
    "الجهات": "contacts",
    "الفيديوهات": "videos",
    "الصوت": "voice"
}

# --- 1. الحماية التلقائية (المنع الفوري) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_protection(event):
    # تخطي الفحص للمنشئ والمدراء والمميزين
    user_rank = db.get_rank(event.chat_id, event.sender_id)
    if user_rank in ["مدير", "مالك", "المنشئ", "مميز"] or event.sender_id == OWNER_ID:
        return

    gid = str(event.chat_id)

    # فحص الروابط والمعرفات (Regex)
    if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+)', event.raw_text):
        await event.delete()
        return

    if db.is_locked(gid, "usernames") and re.search(r'@\S+', event.raw_text):
        await event.delete()
        return

    # فحص الميديا
    if event.photo and db.is_locked(gid, "photos"): await event.delete()
    elif event.sticker and db.is_locked(gid, "stickers"): await event.delete()
    elif event.gif and db.is_locked(gid, "gifs"): await event.delete()
    elif event.fwd_from and db.is_locked(gid, "forward"): await event.delete()
    elif event.video and db.is_locked(gid, "videos"): await event.delete()
    elif event.voice and db.is_locked(gid, "voice"): await event.delete()

# --- 2. أوامر التحكم (قفل / فتح / تعطيل / تفعيل) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def locks_control(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # التحقق من الصلاحية (مدير أو أعلى)
    user_rank = db.get_rank(gid, event.sender_id)
    if user_rank not in ["مدير", "مالك", "المنشئ"] and event.sender_id != OWNER_ID:
        return

    # منطق القفل والفتح
    for ar_name, en_name in FEATURES.items():
        if msg == f"قفل {ar_name}":
            db.toggle_lock(gid, en_name, 1)
            await event.respond(f"🔒 تم قفل **{ar_name}** بنجاح.")
        elif msg == f"فتح {ar_name}":
            db.toggle_lock(gid, en_name, 0)
            await event.respond(f"🔓 تم فتح **{ar_name}** بنجاح.")

    # أوامر التفعيل والتعطيل للأنظمة
    if msg == "تفعيل الترحيب":
        db.set_setting(gid, "welcome_status", "on")
        await event.respond("✅ تم تفعيل نظام الترحيب.")
    elif msg == "تعطيل الترحيب":
        db.set_setting(gid, "welcome_status", "off")
        await event.respond("❌ تم تعطيل نظام الترحيب.")

    if msg == "قفل الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=False)
        await event.respond("🚫 تم قفل الدردشة، لا يمكن للأعضاء الإرسال.")
    elif msg == "فتح الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=True)
        await event.respond("✅ تم فتح الدردشة للجميع.")
