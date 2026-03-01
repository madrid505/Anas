import re
from telethon import events
from database import db
from main import client, ALLOWED_GROUPS, OWNER_ID, check_privilege

# خريطة الميزات (الاسم بالعربي : المفتاح في القاعدة)
FEATURES = {
    "الروابط": "links",
    "الصور": "photos",
    "الملصقات": "stickers",
    "المتحركة": "gifs",
    "التوجيه": "forward",
    "المعرفات": "usernames",
    "الفيديوهات": "videos",
    "البصمات": "voice",
    "الملفات": "files"
}

# --- 1. معالج المنع التلقائي (الذي يحذف الرسائل فوراً) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_protection_handler(event):
    # تخطي الفحص للمدراء، الملاك، المنشئ، والمميزين
    if await check_privilege(event, "مميز"):
        return

    gid = str(event.chat_id)
    msg = event.raw_text

    # فحص الروابط والمعرفات (Regex)
    if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+)', msg):
        await event.delete()
        return

    if db.is_locked(gid, "usernames") and re.search(r'@\S+', msg):
        await event.delete()
        return

    # فحص الميديا (صور، ملصقات، فيديوهات، إلخ)
    if db.is_locked(gid, "photos") and event.photo: await event.delete()
    elif db.is_locked(gid, "stickers") and event.sticker: await event.delete()
    elif db.is_locked(gid, "gifs") and event.gif: await event.delete()
    elif db.is_locked(gid, "forward") and event.fwd_from: await event.delete()
    elif db.is_locked(gid, "videos") and event.video: await event.delete()
    elif db.is_locked(gid, "voice") and event.voice: await event.delete()
    elif db.is_locked(gid, "files") and event.document: await event.delete()

# --- 2. أوامر التحكم باللغة العربية (قفل/فتح) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def locks_control_commands(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # التحقق من الصلاحية (مدير أو أعلى)
    if not await check_privilege(event, "مدير"):
        return

    # التكرار على الخريطة لتنفيذ الأمر (قفل الروابط، فتح الصور، إلخ)
    for ar_name, en_name in FEATURES.items():
        if msg == f"قفل {ar_name}":
            db.toggle_lock(gid, en_name, 1)
            await event.respond(f"🔒 تم قفل **{ar_name}** بنجاح.")
            return
        elif msg == f"فتح {ar_name}":
            db.toggle_lock(gid, en_name, 0)
            await event.respond(f"🔓 تم فتح **{ar_name}** بنجاح.")
            return

    # أوامر قفل وفتح الدردشة (التحكم في صلاحيات المجموعة)
    if msg == "قفل الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=False)
        await event.respond("🚫 تم **قفل الدردشة**، لا يمكن للأعضاء الإرسال.")
    elif msg == "فتح الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=True)
        await event.respond("✅ تم **فتح الدردشة** للجميع.")
