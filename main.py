import random
import re
import asyncio
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد ---
API_ID = 33183154
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

client = TelegramClient('Monopoly_Ultra_V5', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة جلب اللقب بناءً على التفاعل
def get_user_title(count):
    if count > 1000: return "سُلطان مونوبولي 🏆"
    if count > 600: return "أسطورة التفاعل 👑"
    if count > 300: return "متفاعل ذهبي 🥇"
    if count > 150: return "صديق المجموعة 🤝"
    if count > 50: return "متفاعل ناشئ ✨"
    return "عضو جديد 🌱"

# دالة التحقق من الرتبة
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID: return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- نظام الردود الملكية والذكية ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def reactive_replies(event):
    msg = event.raw_text
    uid = event.sender_id
    gid = str(event.chat_id)
    count = db.get_user_messages(gid, uid)
    title = get_user_title(count)
    is_admin = await check_privilege(event, "مدير")

    # ردود "بوت" المتنوعة
    if msg == "بوت":
        res = ["لبيه! ✨", "نعم يا {title} 🌹", "تفضل يا مدير 🫡", "معك مونوبولي الحماية 🛡️"]
        await event.reply(random.choice(res).format(title=title))

    # الردود الترحيبية (ملكياً وعادياً)
    elif msg in ["السلام عليكم", "سلام عليكم", "سلام"]:
        if is_admin:
            await event.reply(f"👑 وعليكم السلام والرحمة يا سيادة المشرف الموقر! نورت المكان.")
        else:
            await event.reply(f"وعليكم السلام والرحمة يا {title} 🌹")

    elif "صباح الخير" in msg:
        await event.reply(f"صباح الورد والجمال يا {title}! يومك سعيد ☀️" if not is_admin else "صباح النور يا مطورنا/مديرنا الغالي 🌸")

    elif "مساء الخير" in msg:
        await event.reply(f"مساء النور والسرور يا {title} ✨" if not is_admin else "أجمل مساء لعيون الإدارة 🌙")

# --- معالج الرسائل الرئيسي (المهام الإدارية) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    uid = event.sender_id
    
    if not event.is_private: db.increase_messages(gid, uid)

    # نظام الردود المبرمجة
    reply_data = db.get_reply_data(gid, msg)
    if reply_data:
        rep_text, media_id = reply_data
        if media_id and media_id != "None":
            await event.reply(rep_text if rep_text else "", file=media_id)
            return
        elif rep_text:
            await event.reply(rep_text)
            return

    # نظام المتفاعلين
    if msg == "المتفاعلين":
        top_users = db.get_top_active(gid, limit=5)
        if not top_users:
            await event.reply("📉 لا يوجد تفاعل مسجل.")
            return
        text = "🏆 **قائمة ملوك التفاعل:**\n"
        for i, u in enumerate(top_users, 1):
            text += f"{i} - `{u[0]}` ⇦ {u[1]} رسالة\n"
        await event.reply(text)

    # نظام الكشف (مع اللقب)
    if msg == "كشف" and event.is_reply:
        reply = await event.get_reply_message()
        user = await client.get_entity(reply.sender_id)
        u_rank = db.get_rank(gid, user.id)
        u_count = db.get_user_messages(gid, user.id)
        u_title = get_user_title(u_count)
        is_banned = "⚠️ محظور!" if db.is_globally_banned(user.id) else "✅ سجل نظيف"
        
        await event.reply(f"🕵️‍♂️ **بطاقة كشف Monopoly**\n━━━━━━━━\n👤 **الاسم:** {user.first_name}\n🆔 **الآيدي:** `{user.id}`\n🎖️ **الرتبة:** {u_rank}\n🏆 **اللقب:** {u_title}\n📈 **المشاركات:** {u_count}\n🛡️ **الحالة:** {is_banned}")

    # أوامر الإدارة (مدير فأعلى)
    if not await check_privilege(event, "مدير"): return

    # نظام "أضف رد" بالخطوات
    if msg == "اضف رد":
        async with client.conversation(event.chat_id, user_id=uid) as conv:
            await conv.send_message("📝 أرسل الآن **الكلمة** التي تريد الرد عليها:")
            word_msg = await conv.get_response()
            word = word_msg.text
            await conv.send_message(f"✅ حسناً، أرسل الآن **الرد** (نص، صورة، ملصق) لـ '{word}':")
            resp_msg = await conv.get_response()
            db.set_reply(gid, word, resp_msg.text if resp_msg.text else "", resp_msg.media)
            await conv.send_message(f"🎉 تم حفظ الرد الذكي لـ '{word}' بنجاح!")

    # أوامر المشرفين (تثبيت، حذف، إلخ) بالرد
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if msg == "تثبيت":
            await client.pin_from_event(event)
            await event.respond("📌 تم تثبيت الرسالة بنجاح.")
        elif msg == "حذف":
            await reply_msg.delete()
            await event.delete()
        elif msg == "طرد":
            await client.kick_participant(gid, reply_msg.sender_id)
            await event.respond("👞 تم طرد المستخدم.")

    if msg == "امر":
        btns = [[Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
                [Button.inline("📜 الأوامر", "show_cmds"), Button.inline("❌ إغلاق", "close")]]
        await event.respond("♥️ Monopoly مونوبولي لوحة تحكم ♥️", buttons=btns)

# نظام الترحيب
@client.on(events.ChatAction)
async def welcome_action(event):
    if event.user_joined or event.user_added:
        gid = str(event.chat_id)
        if db.get_setting(gid, "welcome_status") == "on":
            user = await event.get_user()
            welcome = f"👑 أهلاً بمطورنا أنس!" if user.id == OWNER_ID else f"✨ نورت المجموعة يا {user.first_name}! 🌹"
            await event.respond(welcome)

import ranks, locks, tag, callbacks, cleaner
print("--- [Monopoly V5 - Active & Smart] ---")
client.run_until_disconnected()
