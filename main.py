import random
import re
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, types
from database import db

# --- بيانات الاعتماد الخاصة بالبوت ---
API_ID = 33183154
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKo_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

# تشغيل العميل (Client)
client = TelegramClient('Monopoly_Ultra_V5', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- 1. دالة التصفير التلقائي الأسبوعي ---
async def weekly_auto_reset():
    """
    هذه الدالة تعمل في الخلفية بشكل دائم.
    تنتظر لمدة أسبوع كامل ثم تقوم بمسح بيانات التفاعل لتبدأ المسابقة من جديد.
    """
    while True:
        try:
            # الانتظار لمدة 7 أيام (بالثواني)
            await asyncio.sleep(604800) 
            
            # تنفيذ عملية الحذف من قاعدة البيانات
            db.cursor.execute("DELETE FROM activity")
            db.conn.commit()
            
            # إبلاغ المجموعات المسموحة بعملية التصفير
            for chat_id in ALLOWED_GROUPS:
                try:
                    text_reset = "🔄 **تنبيه ملكي من إدارة Monopoly**\n\nلقد مضى أسبوع من الحماس! تم تصفير عداد المتفاعلين الآن. ابدأوا رحلة الصعود للقمة من جديد! 🏆"
                    await client.send_message(chat_id, text_reset)
                except Exception as e_send:
                    print(f"فشل إرسال رسالة التصفير لـ {chat_id}: {e_send}")
        except Exception as e_reset:
            print(f"خطأ غير متوقع في نظام التصفير: {e_reset}")
            await asyncio.sleep(3600) # إعادة المحاولة بعد ساعة في حال حدوث خطأ

# --- 2. دالة الألقاب التفاعلية التراكمية ---
def get_user_title(count):
    """تحديد لقب العضو بناءً على عدد رسائله في المجموعة"""
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

# --- 3. دالة التحقق من الصلاحيات والرتب ---
async def check_privilege(event, required_rank):
    """تتحقق مما إذا كان المستخدم يملك الرتبة المطلوبة لتنفيذ الأمر"""
    if event.sender_id == OWNER_ID:
        return True
    
    # جلب رتبة العضو من قاعدة البيانات
    current_gid = str(event.chat_id)
    user_rank = db.get_rank(current_gid, event.sender_id)
    
    # ترتيب القوة للرتب
    ranks_order = {
        "عضو": 0, 
        "مميز": 1, 
        "ادمن": 2, 
        "مدير": 3, 
        "مالك": 4, 
        "المنشئ": 5
    }
    
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- 4. نظام الردود الملكية والذكية (الردود التلقائية) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def reactive_replies(event):
    msg_text = event.raw_text
    user_id = event.sender_id
    group_id = str(event.chat_id)
    
    # جلب معلومات العضو للتفاعل الشخصي
    msg_count = db.get_user_messages(group_id, user_id)
    user_title = get_user_title(msg_count)
    is_admin = await check_privilege(event, "مدير")

    # ردود كلمة (بوت) المتنوعة
    if msg_text == "بوت":
        bot_responses = [
            "لبيه! ✨", 
            f"نعم يا {user_title} 🌹", 
            "تفضل يا مديرنا الغالي 🫡", 
            "أمرك مطاع يا بطل مونوبولي", 
            "معك بوت مونوبولي في الخدمة 🛡️",
            "سمّ يا الأمير، كيف أخدمك؟",
            "أبشر بعزك، أنا هنا دائماً 🎩",
            "نعم يا طيب؟ أسمعك جيداً."
        ]
        await event.reply(random.choice(bot_responses))

    # الرد على السلام
    elif msg_text in ["السلام عليكم", "سلام عليكم", "سلام"]:
        if is_admin:
            await event.reply("👑 وعليكم السلام والرحمة يا سيادة المشرف الموقر! نورت المكان بوجودك.")
        else:
            await event.reply(f"وعليكم السلام والرحمة يا {user_title} نورتنا 🌹")

    # الرد على تحية الصباح
    elif "صباح الخير" in msg_text:
        if is_admin:
            await event.reply("صباح النور والسرور يا مطورنا/مديرنا الغالي 🌸")
        else:
            await event.reply(f"صباح الورد والجمال يا {user_title}! أتمنى لك يوماً رائعاً ☀️")

    # الرد على تحية المساء
    elif "مساء الخير" in msg_text:
        if is_admin:
            await event.reply("أجمل مساء لعيون الإدارة الموقرة 🌙")
        else:
            await event.reply(f"مساء النور والسرور يا {user_title} ✨ نورت المجموعة.")

# --- 5. معالج الرسائل والأوامر الرئيسي ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_handler(event):
    message = event.raw_text
    chat_id = str(event.chat_id)
    sender_id = event.sender_id
    
    # 1. تسجيل التفاعل التراكمي
    if not event.is_private:
        db.increase_messages(chat_id, sender_id)

    # 2. نظام الردود المبرمجة (أضف رد)
    custom_reply = db.get_reply_data(chat_id, message)
    if custom_reply:
        rep_text, media_id = custom_reply
        if media_id and media_id != "None":
            await event.reply(rep_text if rep_text else "", file=media_id)
            return
        elif rep_text:
            await event.reply(rep_text)
            return

    # 3. أمر "رتبتي" - لعرض تفاصيل العضو
    if message == "رتبتي":
        my_count = db.get_user_messages(chat_id, sender_id)
        my_title = get_user_title(my_count)
        my_rank = db.get_rank(chat_id, sender_id)
        info_msg = (
            f"📊 **بطاقة تفاصيلك في Monopoly**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎖️ **رتبتك الحالية:** {my_rank}\n"
            f"🏆 **لقبك التفاعلي:** {my_title}\n"
            f"📈 **عدد مشاركاتك:** {my_count} رسالة\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        await event.reply(info_msg)
        return

    # 4. نظام "المتفاعلين" - لوحة الشرف الملكية
    if message == "المتفاعلين":
        top_list = db.get_top_active(chat_id, limit=5)
        if not top_list:
            await event.reply("📉 لا توجد بيانات تفاعل مسجلة حالياً.")
            return

        king_uid, king_msgs = top_list[0]
        try:
            king_entity = await client.get_entity(int(king_uid))
            king_name = king_entity.first_name
        except:
            king_name = "مستخدم غير معروف"

        sharaf_text = (
            f"🏆 **سُلطان التفاعل في Monopoly** 🏆\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ **تهانينا لـ 'فارس الكلمة' لهذا الأسبوع!** ✨\n\n"
            f"👤 **المتفاعل الملك:** {king_name}\n"
            f"🆔 **الآيدي:** `{king_uid}`\n"
            f"📈 **رصيد المشاركات:** `{king_msgs}` رسالة ذهبية\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎖️ **كلمة الإدارة:**\n"
            f"\"شكراً لكونك جزءاً فعالاً في عائلة مونوبولي.\"\n\n"
            f"💡 *ملاحظة: يتم تصفير العداد تلقائياً كل أسبوع!*"
        )
        await event.reply(sharaf_text)

    # 5. نظام "كشف" - بالرد على العضو
    if message == "كشف" and event.is_reply:
        reply_msg = await event.get_reply_message()
        target_user = await client.get_entity(reply_msg.sender_id)
        t_rank = db.get_rank(chat_id, target_user.id)
        t_count = db.get_user_messages(chat_id, target_user.id)
        t_title = get_user_title(t_count)
        t_time = datetime.now().strftime("%I:%M %p")
        
        kashf_text = (
            f"🕵️‍♂️ **| بطاقة كشف Monopoly**\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** {target_user.first_name}\n"
            f"🆔 **الآيدي:** `{target_user.id}`\n"
            f"🎖️ **الرتبة:** {t_rank}\n"
            f"🏆 **اللقب:** {t_title}\n"
            f"📈 **المشاركات:** {t_count}\n"
            f"🕒 **التوقيت:** {t_time}\n"
            f"🛡️ **الحالة:** سجل نظيف ✅\n"
            f"━━━━━━━━━━━━━━"
        )
        await event.reply(kashf_text)

    # تحقق من صلاحيات الإدارة للأوامر القادمة
    if not await check_privilege(event, "مدير"):
        return

    # 6. نظام "أضف رد" المطور (بدون تداخل)
    if message == "اضف رد":
        try:
            async with client.conversation(event.chat_id, timeout=60) as conv:
                await conv.send_message("📝 **أهلاً بك يا مدير!**\nأرسل الآن **الكلمة** التي تريد الرد عليها:")
                response_word = await conv.get_response()
                # ضمان أن البوت لا يسمع إلا صاحب الأمر
                if response_word.sender_id != sender_id:
                     return 
                
                word_to_save = response_word.text
                await conv.send_message(f"✅ ممتاز، الآن أرسل **الرد** (نص، صورة، ملصق) لـ '{word_to_save}':")
                response_val = await conv.get_response()
                if response_val.sender_id != sender_id:
                     return

                db.set_reply(chat_id, word_to_save, response_val.text if response_val.text else "", response_val.media)
                await conv.send_message("تمت اضافة الرد بنجاح يا مديرنا الغالي 👑")
        except asyncio.TimeoutError:
            await event.reply("⚠️ انتهى الوقت، يرجى إعادة المحاولة.")
        except Exception as e_conv:
            print(f"Error in convo: {e_conv}")

    # 7. أوامر التحكم بالرسائل (بالرد)
    if event.is_reply:
        target_msg = await event.get_reply_message()
        if message == "تثبيت":
            # استخدام الطريقة الرسمية لتجنب خطأ الـ Logs
            await client.pin_message(event.chat_id, target_msg.id)
            await event.respond("📌 تم تثبيت الرسالة بنجاح.")
        elif message == "حذف":
            await target_msg.delete()
            await event.delete()
        elif message == "طرد":
            await client.kick_participant(event.chat_id, target_msg.sender_id)
            await event.respond("👞 تم طرد المستخدم بنجاح.")

    # 8. فتح لوحة الأوامر
    if message == "امر":
        buttons_list = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("📜 الأوامر", "show_cmds"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.respond("♥️ Monopoly مونوبولي لوحة تحكم ♥️", buttons=buttons_list)

# --- 6. نظام الترحيب والعمليات التلقائية ---
@client.on(events.ChatAction)
async def welcome_action(event):
    if event.user_joined or event.user_added:
        current_gid = str(event.chat_id)
        new_user = await event.get_user()
        
        # ترحيب خاص بالمطور أنس
        if new_user.id == OWNER_ID:
            await event.respond("👑 نورت المجموعة بطلتك يا مطورنا أنس! انحنوا للملك.")
        elif db.get_setting(current_gid, "welcome_status") == "on":
            await event.respond(f"✨ نورت المجموعة يا {new_user.first_name}! ننتظر تفاعلك 🌹")

# --- استدعاء الموديولات المساعدة ---
import ranks, locks, tag, callbacks, cleaner

# تشغيل المهمة الأسبوعية في الخلفية
client.loop.create_task(weekly_auto_reset())

# بدء التشغيل النهائي
print("--- [Monopoly System Online - V5.8 Royal Edition] ---")
print("--- [Status: Complete | Maintenance: Fixed] ---")

client.run_until_disconnected()
