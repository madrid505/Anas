import random
import re
import asyncio
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد الخاصة بك ---
API_ID = '25736711'
API_HASH = '809081e792461f52b8265a73e13d5b00'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# تشغيل البوت بجلسة فريدة لضمان استقرار قاعدة البيانات
client = TelegramClient('AnasMegaSession', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- دالة التحقق من الرتبة عالمياً ---
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID:
        return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- 1. نظام الردود العشوائية عند مناداة "بوت" ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^بوت$"))
async def bot_random_replies(event):
    replies = [
        "هلا عيني، تفضل؟ 🌹",
        "البوت في خدمتك يا مدير. 🫡",
        "نعم، من ينادي؟ 🤔",
        "لبيه! اؤمرني بشيء؟ ✨",
        "معك بوت الحماية المتكامل، كيف أساعدك؟ 🛡️",
        "عيوني لك، اطلب وتمنى! 🌟"
    ]
    await event.reply(random.choice(replies))

# --- 2. معالج الأوامر العامة والردود المضافة يدوياً ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def global_commands_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # التحقق من الردود الشخصية المضافة (اضف رد)
    custom_reply_text = db.get_reply(gid, msg)
    if custom_reply_text:
        await event.reply(custom_reply_text)
        return

    # التحقق من الصلاحية (يجب أن يكون مدير فأعلى للأوامر التالية)
    if not await check_privilege(event, "مدير"):
        return

    # فتح قائمة الأوامر (لوحة تحكم تون)
    if msg == "امر":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.respond("⬇️ **لوحة تحكم بوت الأساطير (نظام TON المتكامل):**", buttons=btns)

    # أوامر التثبيت (بالرد)
    elif msg == "تثبيت" and event.is_reply:
        reply_to_msg = await event.get_reply_message()
        await client.pin_from_id(event.chat_id, reply_to_msg.id)
        await event.respond("✅ **تم تثبيت الرسالة بنجاح في المجموعة.**")
    
    elif msg == "الغاء التثبيت":
        await client.unpin_from_id(event.chat_id)
        await event.respond("🔓 **تم إلغاء تثبيت الرسالة.**")

    # إدارة الردود (اضف رد / مسح رد)
    elif msg.startswith("اضف رد "):
        parts = msg.split(" ", 2)
        if len(parts) == 3:
            db.set_reply(gid, parts[1], parts[2])
            await event.respond(f"✅ تم إضافة الرد التلقائي بنجاح:\n▫️ الكلمة: **{parts[1]}**\n▫️ الرد: **{parts[2]}**")

    elif msg.startswith("مسح رد "):
        word_to_delete = msg.replace("مسح رد ", "").strip()
        db.delete_reply(gid, word_to_delete)
        await event.respond(f"🗑️ تم حذف الرد الخاص بالكلمة: **{word_to_delete}**")

    # إعدادات نظام الترحيب
    elif msg == "تفعيل الترحيب":
        db.set_setting(gid, "welcome_status", "on")
        await event.respond("✅ **تم تفعيل نظام الترحيب بالأعضاء الجدد.**")
    
    elif msg == "تعطيل الترحيب":
        db.set_setting(gid, "welcome_status", "off")
        await event.respond("❌ **تم تعطيل نظام الترحيب.**")

# --- 3. نظام الترحيب التلقائي عند انضمام عضو ---
@client.on(events.ChatAction)
async def automatic_welcome(event):
    if event.user_joined or event.user_added:
        gid = str(event.chat_id)
        if db.get_setting(gid, "welcome_status") == "on":
            joined_user = await event.get_user()
            welcome_msg = f"✨ نورت المجموعة يا {joined_user.first_name}!\n🆔 آيديك: `{joined_user.id}`\n📅 بالتوفيق لك معنا! 🌹"
            await event.respond(welcome_msg)

# --- 4. استدعاء الموديولات المكملة (إلزامي في نهاية الملف) ---
import ranks
import locks
import tag
import callbacks
import cleaner

print("--- [نظام TON الاحترافي الشامل يعمل الآن بكافة طاقته] ---")
client.run_until_disconnected()
