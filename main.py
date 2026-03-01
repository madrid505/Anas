import random
import re
import asyncio
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد الجديدة والمصححة ---
API_ID = 33183154
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# بدء تشغيل العميل
client = TelegramClient('AnasFinalSessionV3', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة التحقق من الرتبة عالمياً
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID:
        return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# الرد التلقائي عند مناداة "بوت"
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^بوت$"))
async def bot_talk(event):
    replies = ["لبيه! ✨", "هلا عيني 🌹", "تفضل يا مدير 🫡", "نعم، معك بوت الحماية 🛡️"]
    await event.reply(random.choice(replies))

# معالج الردود والوظائف الأساسية
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # 1. نظام الردود (نصوص وميديا)
    reply_data = db.get_reply_data(gid, msg)
    if reply_data:
        rep_text, media_id = reply_data
        if media_id and media_id != "None":
            await event.reply(rep_text if rep_text else "", file=media_id)
            return
        elif rep_text:
            await event.reply(rep_text)
            return

    # أوامر الإدارة (مدير فأعلى)
    if not await check_privilege(event, "مدير"):
        return

    # فتح قائمة الأوامر
    if msg == "امر":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.respond("⬇️ **لوحة تحكم بوت الأساطير (نظام TON):**", buttons=btns)

    # أمر التثبيت
    elif msg == "تثبيت" and event.is_reply:
        reply = await event.get_reply_message()
        await client.pin_from_id(event.chat_id, reply.id)
        await event.respond("📌 تم التثبيت بنجاح.")

    # نظام إضافة الردود المتطور (نص أو ميديا)
    elif msg.startswith("اضف رد "):
        word = msg.replace("اضف رد ", "").strip()
        
        # إذا كان هناك رد (Reply) على ميديا (صورة/فيديو/الخ)
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg.media:
                db.set_reply(gid, word, reply_msg.text if reply_msg.text else "", reply_msg.media)
                await event.respond(f"✅ تم حفظ الرد (ميديا) للكلمة: **{word}**")
                return

        # إذا كان الرد نصياً مباشراً
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            db.set_reply(gid, parts[1], parts[2])
            await event.respond(f"✅ تم حفظ الرد (نصي) لـ: **{parts[1]}**")

    # مسح الرد
    elif msg.startswith("مسح رد "):
        word = msg.replace("مسح رد ", "").strip()
        db.delete_reply(gid, word)
        await event.respond(f"🗑️ تم حذف الرد لـ: **{word}**")

    # تفعيل وتعطيل الترحيب
    elif msg == "تفعيل الترحيب":
        db.set_setting(gid, "welcome_status", "on")
        await event.respond("✅ تم تفعيل الترحيب.")
    
    elif msg == "تعطيل الترحيب":
        db.set_setting(gid, "welcome_status", "off")
        await event.respond("❌ تم تعطيل الترحيب.")

# نظام الترحيب التلقائي
@client.on(events.ChatAction)
async def welcome_action(event):
    if (event.user_joined or event.user_added):
        gid = str(event.chat_id)
        if db.get_setting(gid, "welcome_status") == "on":
            user = await event.get_user()
            await event.respond(f"✨ نورت المجموعة يا {user.first_name}! 🌹")

# استدعاء الموديولات الخارجية
import ranks, locks, tag, callbacks, cleaner

print("--- [سورس TON يعمل الآن بكامل طاقته - 100%] ---")
client.run_until_disconnected()
