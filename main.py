import random
import re
from telethon import TelegramClient, events, Button
from database import db
# استيراد الموديولات المنفصلة
import ranks, locks, tag, callbacks , cleaner

# --- بيانات الاعتماد الخاصة بك ---
API_ID = '33183154'
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

client = TelegramClient('AnasBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- نظام الردود العشوائية (مثل تون) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^بوت$"))
async def bot_random_replies(event):
    replies = [
        "هلا عيني، تفضل؟ 🌹",
        "البوت في خدمتك يا مدير. 🫡",
        "نعم، من ينادي؟ 🤔",
        "لبيه! اؤمرني بشيء؟ ✨",
        "معك بوت الحماية المتكامل، كيف أساعدك؟ 🛡️"
    ]
    await event.reply(random.choice(replies))

# --- نظام الترحيب التلقائي ---
@client.on(events.ChatAction)
async def welcome_handler(event):
    if event.user_joined or event.user_added:
        # التحقق إذا كان الترحيب مفعلاً في المجموعة
        if db.get_setting(str(event.chat_id), "welcome_status") == "on":
            user = await event.get_user()
            welcome_msg = db.get_welcome(str(event.chat_id)) or "نورت المجموعة يا {الاسم}"
            final_msg = welcome_msg.replace("{الاسم}", user.first_name).replace("{الاي دي}", str(user.id))
            await event.respond(final_msg)

# --- أوامر الإدارة العامة (تثبيت، ردود، كشف) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def general_admin_commands(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # التحقق من الرتبة (مدير أو أعلى)
    user_rank = db.get_rank(gid, event.sender_id)
    if user_rank not in ["مدير", "مالك", "المنشئ"] and event.sender_id != OWNER_ID:
        return

    # التثبيت وإلغاء التثبيت
    if msg == "تثبيت" and event.is_reply:
        reply = await event.get_reply_message()
        await client.pin_from_id(event.chat_id, reply.id)
        await event.respond("📌 تم تثبيت الرسالة بنجاح")
    
    elif msg == "الغاء التثبيت":
        await client.unpin_from_id(event.chat_id)
        await event.respond("🔓 تم إلغاء التثبيت")

    # إضافة رد ومسح رد
    elif msg.startswith("اضف رد "):
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            db.set_reply(gid, parts[1], parts[2])
            await event.respond(f"✅ تم إضافة الرد للكلمة: {parts[1]}")

    elif msg.startswith("مسح رد "):
        word = msg.replace("مسح رد ", "")
        db.delete_reply(gid, word)
        await event.respond(f"🗑️ تم حذف الرد للكلمة: {word}")

# تشغيل البوت
print("--- سورس TON المطور يعمل الآن بكافة الموديولات ---")
client.run_until_disconnected()
