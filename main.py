import random
import re
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد ---
API_ID = 33183154
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# تشغيل البوت
client = TelegramClient('Monopoly_Ultra_V5', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- 1. دالة التصفير التلقائي الأسبوعي (الجديدة) ---
async def weekly_auto_reset():
    """تقوم هذه الدالة بتصفير عداد التفاعل تلقائياً كل 7 أيام"""
    while True:
        try:
            # ننتظر لمدة أسبوع كامل (604800 ثانية)
            await asyncio.sleep(604800) 
            
            # تنفيذ عملية المسح في قاعدة البيانات
            db.cursor.execute("DELETE FROM activity")
            db.conn.commit()
            
            # إرسال تنبيه للمجموعات المسموحة (اختياري)
            for chat_id in ALLOWED_GROUPS:
                await client.send_message(chat_id, "🔄 **تنبيه الإدارة:**\nتم تصفير عداد التفاعل بنجاح! ابدأوا منافسة جديدة الآن. 🏆")
        except Exception as e:
            print(f"خطأ في نظام التصفير: {e}")
            await asyncio.sleep(3600) # إعادة المحاولة بعد ساعة في حال الخطأ

# --- 2. دالة الألقاب التفاعلية ---
def get_user_title(count):
    if count > 1000:
        return "سُلطان مونوبولي 🏆"
    elif count > 600:
        return "أسطورة التفاعل 👑"
    elif count > 300:
        return "متفاعل ذهبي 🥇"
    elif count > 150:
        return "صديق المجموعة 🤝"
    elif count > 50:
        return "متفاعل ناشئ ✨"
    else:
        return "عضو جديد 🌱"

# --- 3. دالة التحقق من الرتبة ---
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID:
        return True
    user_rank = db.get_rank(str(event.chat_id), event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- 4. نظام الردود الملكية والذكية ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def reactive_replies(event):
    msg = event.raw_text
    uid = event.sender_id
    gid = str(event.chat_id)
    count = db.get_user_messages(gid, uid)
    title = get_user_title(count)
    is_admin = await check_privilege(event, "مدير")

    if msg == "بوت":
        res = ["لبيه! ✨", "نعم يا {title} 🌹", "تفضل يا مدير 🫡", "أمرك مطاع يا غالي", "معك مونوبولي 🛡️"]
        await event.reply(random.choice(res).format(title=title))

    elif msg in ["السلام عليكم", "سلام عليكم", "سلام"]:
        if is_admin:
            await event.reply(f"👑 وعليكم السلام والرحمة يا سيادة المشرف الموقر! نورت المكان.")
        else:
            await event.reply(f"وعليكم السلام والرحمة يا {title} 🌹")

    elif "صباح الخير" in msg:
        if is_admin:
            await event.reply("صباح النور يا مطورنا الغالي 🌸")
        else:
            await event.reply(f"صباح الورد والجمال يا {title}! يومك سعيد ☀️")

    elif "مساء الخير" in msg:
        if is_admin:
            await event.reply("أجمل مساء لعيون الإدارة 🌙")
        else:
            await event.reply(f"مساء النور والسرور يا {title} ✨")

# --- 5. معالج الرسائل الرئيسي ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    uid = event.sender_id
    
    if not event.is_private:
        db.increase_messages(gid, uid)

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
            f"💡 *ملاحظة: يتم تصفير العداد تلقائياً كل أسبوع لفتح المنافسة!*"
        )
        await event.reply(text)

    # --- نظام الكشف الملكي ---
    if msg == "كشف" and event.is_reply:
        reply = await event.get_reply_message()
        user = await client.get_entity(reply.sender_id)
        u_rank = db.get_rank(gid, user.id)
        u_count = db.get_user_messages(gid, user.id)
        u_title = get_user_title(u_count)
        now_time = datetime.now().strftime("%I:%M %p")
        is_banned = "⚠️ محظور سابقاً!" if db.is_globally_banned(user.id) else "✅ سجل نظيف"
        
        info_text = (
            f"🕵️‍♂️ **| بطاقة كشف العضو (Monopoly)**\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** {user.first_name}\n"
            f"🆔 **الآيدي:** `{user.id}`\n"
            f"🎖️ **الرتبة:** {u_rank}\n"
            f"🏆 **اللقب:** {u_title}\n"
            f"📈 **المشاركات:** {u_count}\n"
            f"🕒 **التوقيت:** {now_time}\n"
            f"🛡️ **الحالة:** {is_banned}\n"
            f"━━━━━━━━━━━━━━"
        )
        await event.reply(info_text)

    if not await check_privilege(event, "مدير"):
        return

    # --- نظام أضف رد (محادثة الخطوات) ---
    if msg == "اضف رد":
        async with client.conversation(event.chat_id, user_id=uid) as conv:
            await conv.send_message("📝 أرسل الآن **الكلمة** التي تريد الرد عليها (العنوان):")
            word_msg = await conv.get_response()
            word_text = word_msg.text
            
            await conv.send_message(f"✅ ممتاز، الآن أرسل **الرد** لـ '{word_text}':")
            response_msg = await conv.get_response()
            
            db.set_reply(gid, word_text, response_msg.text if response_msg.text else "", response_msg.media)
            await conv.send_message("تمت اضافة الرد بنجاح يا مديرنا الغالي 👑")

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
            await event.respond("👞 تم طرد المستخدم بنجاح.")

    if msg == "امر":
        btns = [[Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
                [Button.inline("📜 الأوامر", "show_cmds"), Button.inline("❌ إغلاق", "close")]]
        await event.respond("♥️ Monopoly مونوبولي لوحة تحكم ♥️", buttons=btns)

# --- 6. نظام الترحيب والعمليات الملكية ---
@client.on(events.ChatAction)
async def welcome_action(event):
    if event.user_joined or event.user_added:
        gid = str(event.chat_id)
        user = await event.get_user()
        if user.id == OWNER_ID:
            await event.respond("👑 نورت المجموعة بطلتك يا مطورنا أنس! انحنوا للملك.")
        elif db.get_setting(gid, "welcome_status") == "on":
            await event.respond(f"✨ نورت المجموعة يا {user.first_name}! 🌹")

# استدعاء الموديولات المساعدة
import ranks, locks, tag, callbacks, cleaner

# تشغيل مهام الخلفية (التصفير التلقائي)
client.loop.create_task(weekly_auto_reset())

print("--- [Monopoly System Online - V5.5 Royal Edition] ---")
client.run_until_disconnected()
