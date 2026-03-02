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

# تغيير اسم الجلسة لكسر الحظر السابق (استخدم V5 للضمان)
client = TelegramClient('Monopoly_Ultra_V5', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة التحقق من الرتبة
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID:
        return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# الرد التلقائي "بوت"
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^بوت$"))
async def bot_talk(event):
    replies = ["لبيه! ✨", "هلا عيني 🌹", "تفضل يا مدير 🫡", "نعم، معك بوت Monopoly 🛡️"]
    await event.reply(random.choice(replies))

# معالج الرسائل الرئيسي
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    uid = event.sender_id
    
    # زيادة عداد التفاعل تلقائياً
    if not event.is_private:
        db.increase_messages(gid, uid)

    # نظام الردود الذكي
    reply_data = db.get_reply_data(gid, msg)
    if reply_data:
        rep_text, media_id = reply_data
        if media_id and media_id != "None":
            await event.reply(rep_text if rep_text else "", file=media_id)
            return
        elif rep_text:
            await event.reply(rep_text)
            return

    # --- نظام ملك التفاعل الفخم ---
    if msg == "المتفاعلين":
        top_users = db.get_top_active(gid, limit=5)
        if not top_users:
            await event.reply("📉 لا يوجد تفاعل مسجل بعد.")
            return

        # جلب بيانات المركز الأول (الملك)
        king_id, king_count = top_users[0]
        try:
            king_user = await client.get_entity(int(king_id))
            king_name = king_user.first_name
        except:
            king_name = "مستخدم غير معروف"

        text = (
            f"🏆 **سُلطان التفاعل في Monopoly** 🏆\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ **تهانينا لـ 'فارس الكلمة' لهذا الأسبوع!** ✨\n\n"
            f"👤 **المتفاعل الملك:** {king_name}\n"
            f"🆔 **الآيدي:** `{king_id}`\n"
            f"📈 **رصيد المشاركات:** `{king_count}` رسالة ذهبية\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎖️ **كلمة الإدارة:**\n"
            f"\"التفاعل هو الروح التي تحيي مجموعتنا. شكراً لكونك جزءاً فعالاً في عائلة مونوبولي.\"\n\n"
            f"💡 *ملاحظة: يتم تصفير العداد أسبوعياً لفتح باب المنافسة من جديد!*"
        )
        await event.reply(text)

    # --- نظام الكشف الملكي ---
    if msg == "كشف" and event.is_reply:
        reply = await event.get_reply_message()
        user = await client.get_entity(reply.sender_id)
        u_rank = db.get_rank(gid, user.id)
        msgs_count = db.get_user_messages(gid, user.id)
        is_banned = "⚠️ محظور سابقاً!" if db.is_globally_banned(user.id) else "✅ سجل نظيف"
        
        info_text = (
            f"🕵️‍♂️ **| بطاقة كشف العضو (Monopoly)**\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** {user.first_name}\n"
            f"🆔 **الآيدي:** `{user.id}`\n"
            f"💎 **اليوزر:** @{user.username if user.username else 'لا يوجد'}\n"
            f"🎖️ **الرتبة:** {u_rank}\n"
            f"📈 **المشاركات:** {msgs_count}\n"
            f"🛡️ **الحالة:** {is_banned}\n"
            f"━━━━━━━━━━━━━━"
        )
        await event.reply(info_text)

    # أوامر الإدارة
    if not await check_privilege(event, "مدير"):
        return

    if msg == "امر":
        btns = [[Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
                [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]]
        await event.respond("♥️ Monopoly مونوبولي لوحة تحكم ♥️", buttons=btns)

    elif msg.startswith("اضف رد "):
        word = msg.replace("اضف رد ", "").strip()
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            db.set_reply(gid, word, reply_msg.text if reply_msg.text else "", reply_msg.media)
            await event.respond(f"✅ تم حفظ الرد للكلمة: **{word}**")

# نظام الترحيب
@client.on(events.ChatAction)
async def welcome_action(event):
    if (event.user_joined or event.user_added):
        gid = str(event.chat_id)
        if db.get_setting(gid, "welcome_status") == "on":
            user = await event.get_user()
            if user.id == OWNER_ID:
                await event.respond(f"👑 **أهلاً بك يا مطوري العزيز أنس! نورت Monopoly.** 🌹")
            else:
                await event.respond(f"✨ نورت المجموعة يا {user.first_name}! 🌹")

# استدعاء الموديولات
import ranks, locks, tag, callbacks, cleaner

print("--- [Monopoly System Online - V5] ---")
client.run_until_disconnected()
