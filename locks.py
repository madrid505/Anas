import re
from telethon import events
from database import db
import main  # الوصول لـ client و check_privilege و ALLOWED_GROUPS

# خريطة الميزات (الاسم بالعربي : المفتاح في القاعدة) لسهولة التكرار
FEATURES = {
    "الروابط": "links",
    "الصور": "photos",
    "الملصقات": "stickers",
    "المتحركة": "gifs",
    "التوجيه": "forward",
    "المعرفات": "usernames",
    "الفيديوهات": "videos",
    "البصمات": "voice",
    "الملفات": "files",
    "الجهات": "contacts"
}

# --- 1. معالج الحذف التلقائي (التنفيذ الفوري) ---
@main.client.on(events.NewMessage(chats=main.ALLOWED_GROUPS))
async def auto_protection_handler(event):
    # استثناء الإدمنية والمميزين من الحذف التلقائي
    if await main.check_privilege(event, "مميز"):
        return

    gid = str(event.chat_id)
    msg = event.raw_text

    # فحص الروابط (Regex)
    if db.is_locked(gid, "links"):
        if re.search(r'(https?://\S+|t\.me/\S+|www\.\S+)', msg):
            await event.delete()
            return

    # فحص المعرفات (@)
    if db.is_locked(gid, "usernames"):
        if re.search(r'@\S+', msg):
            await event.delete()
            return

    # فحص الوسائط والميديا
    if db.is_locked(gid, "photos") and event.photo:
        await event.delete()
    elif db.is_locked(gid, "stickers") and event.sticker:
        await event.delete()
    elif db.is_locked(gid, "gifs") and event.gif:
        await event.delete()
    elif db.is_locked(gid, "forward") and event.fwd_from:
        await event.delete()
    elif db.is_locked(gid, "videos") and event.video:
        await event.delete()
    elif db.is_locked(gid, "voice") and event.voice:
        await event.delete()
    elif db.is_locked(gid, "files") and event.document and not event.voice and not event.video:
        await event.delete()
    elif db.is_locked(gid, "contacts") and event.contact:
        await event.delete()

# --- 2. أوامر التحكم الإداري (قفل / فتح) ---
@main.client.on(events.NewMessage(chats=main.ALLOWED_GROUPS))
async def locks_control_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # التحقق من أن المرسل مدير فأعلى
    if not await main.check_privilege(event, "مدير"):
        return

    # معالجة أوامر القفل والفتح لجميع الميزات
    for ar_name, en_key in FEATURES.items():
        if msg == f"قفل {ar_name}":
            db.toggle_lock(gid, en_key, 1)
            await event.respond(f"🔒 تم قفل **{ar_name}** بنجاح.")
            return
        elif msg == f"فتح {ar_name}":
            db.toggle_lock(gid, en_key, 0)
            await event.respond(f"🔓 تم فتح **{ar_name}** بنجاح.")
            return

    # --- 3. أوامر خاصة بالدردشة (قفل/فتح المجموعة) ---
    if msg == "قفل الدردشة":
        try:
            await main.client.edit_permissions(event.chat_id, send_messages=False)
            await event.respond("🚫 تم **إغلاق الدردشة**، لا يمكن للأعضاء الإرسال الآن.")
        except Exception as e:
            await event.respond("❌ فشل قفل الدردشة، تأكد من صلاحيات البوت.")
            
    elif msg == "فتح الدردشة":
        try:
            await main.client.edit_permissions(event.chat_id, send_messages=True)
            await event.respond("✅ تم **فتح الدردشة** للجميع.")
        except Exception as e:
            await event.respond("❌ فشل فتح الدردشة.")

    # --- 4. أمر الوسائط (لقفل/فتح كل شيء دفعة واحدة) ---
    elif msg == "قفل الوسائط":
        media_list = ["photos", "videos", "stickers", "gifs", "voice", "files"]
        for m in media_list:
            db.toggle_lock(gid, m, 1)
        await event.respond("🔒 تم قفل **جميع الوسائط** في المجموعة.")
        
    elif msg == "فتح الوسائط":
        media_list = ["photos", "videos", "stickers", "gifs", "voice", "files"]
        for m in media_list:
            db.toggle_lock(gid, m, 0)
        await event.respond("🔓 تم فتح **جميع الوسائط** في المجموعة.")
