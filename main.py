import random
import re
import asyncio
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد الخاصة بك ---
API_ID = '33183154'
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# تشغيل المحرك
client = TelegramClient('AnasBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- دالة التحقق من الرتبة عالمياً ---
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID: return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- 1. نظام الردود العشوائية والذكية ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^بوت$"))
async def bot_random_replies(event):
    replies = ["لبيه! اؤمرني بشيء؟ ✨", "هلا عيني، تفضل؟ 🌹", "البوت في خدمتك يا مدير. 🫡"]
    await event.reply(random.choice(replies))

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def custom_replies_handler(event):
    # الردود التي يضيفها المدير (اضف رد)
    reply_text = db.get_reply(str(event.chat_id), event.raw_text)
    if reply_text:
        await event.reply(reply_text)

# --- 2. نظام الترحيب التلقائي ---
@client.on(events.ChatAction)
async def welcome_handler(event):
    if event.user_joined or event.user_added:
        gid = str(event.chat_id)
        if db.get_setting(gid, "welcome_status") == "on":
            user = await event.get_user()
            welcome_text = db.get_setting(gid, "welcome_msg") or "✨ نورت المجموعة يا {الاسم}!\n🆔 آيديك: `{الاي دي}`"
            final_msg = welcome_text.replace("{الاسم}", user.first_name).replace("{الاي دي}", str(user.id))
            await event.respond(final_msg)

# --- 3. أوامر الإدارة الشاملة (تثبيت، ردود، تفعيل) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def admin_commands(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    if not await check_privilege(event, "مدير"): return

    # فتح قائمة الأوامر
    if msg == "امر":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.respond("⬇️ **لوحة تحكم بوت الأساطير (نظام TON):**", buttons=btns)

    # أوامر التثبيت
    elif msg == "تثبيت" and event.is_reply:
        reply = await event.get_reply_message()
        await client.pin_from_id(event.chat_id, reply.id)
        await event.respond("📌 تم تثبيت الرسالة بنجاح.")
    
    elif msg == "الغاء التثبيت":
        await client.unpin_from_id(event.chat_id)
        await event.respond("🔓 تم إلغاء التثبيت.")

    # إدارة الردود (اضف رد / مسح رد)
    elif msg.startswith("اضف رد "):
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            db.set_reply(gid, parts[1], parts[2])
            await event.respond(f"✅ تم إضافة الرد للكلمة: **{parts[1]}**")

    elif msg.startswith("مسح رد "):
        word = msg.replace("مسح رد ", "")
        db.delete_reply(gid, word)
        await event.respond(f"🗑️ تم حذف الرد للكلمة: **{word}**")

    # تفعيل وتعطيل الأنظمة
    elif msg == "تفعيل الترحيب":
        db.set_setting(gid, "welcome_status", "on")
        await event.respond("✅ تم تفعيل نظام الترحيب.")
    
    elif msg == "تعطيل الترحيب":
        db.set_setting(gid, "welcome_status", "off")
        await event.respond("❌ تم تعطيل نظام الترحيب.")

# --- 4. استدعاء الموديولات المتخصصة (إلزامي في النهاية) ---
import ranks
import locks
import tag
import callbacks
import cleaner

print("--- [سورس TON الاحترافي يعمل الآن بكافة طاقته] ---")
client.run_until_disconnected()
