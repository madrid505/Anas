import re
import io
from telethon import events, types
from database import db
from hasher import get_image_hash
# التعديل الجوهري لمنع تعليق قاعدة البيانات (Circular Import)
from __main__ import client, ALLOWED_GROUPS, check_privilege 

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
    "الجهات": "contacts",
    "الاباحية": "anti_nsfw"
}

# --- 1. معالج الحذف التلقائي (التنفيذ الفوري) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_protection_handler(event):
    # استثناء الإدمنية والمميزين من الحذف التلقائي لضمان مرونة الإدارة
    if await check_privilege(event, "مميز"):
        return

    gid = str(event.chat_id)
    msg = event.raw_text or "" 

    try:
        # فحص الروابط (Regex مطور ليشمل كل الصيغ)
        if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+|www\.\S+)', msg):
            await event.delete()
            return

        # فحص المعرفات (@) التي قد تستخدم للإعلان
        if db.is_locked(gid, "usernames") and re.search(r'@\S+', msg):
            await event.delete()
            return

        # --- نظام فحص البصمة الذكي (NSFW Protection) ---
        if event.photo:
            photo_bytes = await event.download_media(file=io.BytesIO())
            img_hash = get_image_hash(photo_bytes)
            if db.is_image_blacklisted(img_hash):
                await event.delete()
                return

        # فحص الوسائط والميديا (تحديث الفحص ليكون أكثر دقة)
        if db.is_locked(gid, "photos") and isinstance(event.media, types.MessageMediaPhoto):
            await event.delete()
        elif db.is_locked(gid, "stickers") and event.sticker:
            await event.delete()
        elif db.is_locked(gid, "gifs") and event.gif:
            await event.delete()
        elif db.is_locked(gid, "forward") and event.fwd_from:
            await event.delete()
        elif db.is_locked(gid, "videos") and (event.video or event.video_note):
            await event.delete()
        elif db.is_locked(gid, "voice") and event.voice:
            await event.delete()
        elif db.is_locked(gid, "files") and event.document and not (event.voice or event.video or event.gif or event.sticker):
            await event.delete()
        elif db.is_locked(gid, "contacts") and event.contact:
            await event.delete()
    except Exception: pass 

# --- 2. أوامر التحكم الإداري (قفل / فتح) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def locks_control_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    if not await check_privilege(event, "مدير"):
        return

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
            await client.edit_permissions(event.chat_id, send_messages=False)
            await event.respond("🚫 تم **إغلاق الدردشة**، لا يمكن للأعضاء الإرسال الآن.")
        except Exception:
            await event.respond("❌ فشل قفل الدردشة، تأكد من صلاحيات البوت.")
            
    elif msg == "فتح الدردشة":
        try:
            await client.edit_permissions(event.chat_id, send_messages=True)
            await event.respond("✅ تم **فتح الدردشة** للجميع.")
        except Exception:
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
