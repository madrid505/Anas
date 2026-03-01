import re
from telethon import events, types
from database import db
from main import client, ALLOWED_GROUPS, OWNER_ID, check_privilege

# --- 1. أوامر الرفع والتنزيل (الرتب) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def ranking_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # يجب أن يكون الأمر بالرد على شخص
    if not event.is_reply: return
    
    # التحقق من صلاحية المرسل (يجب أن يكون مالك أو منشئ لرفع الآخرين)
    if not await check_privilege(event, "مالك"): return

    reply = await event.get_reply_message()
    tid = str(reply.sender_id)
    user = await reply.get_sender()
    name = user.first_name if user else "العضو"

    # مصفوفة أوامر الرفع الذكية (Regex)
    if re.match(r"^(رفع مالك|ارفع مالك)$", msg):
        db.set_rank(gid, tid, "مالك")
        await event.respond(f"👑 تم رفع **{name}** ليكون **مالكاً** في البوت.")
        
    elif re.match(r"^(رفع مدير|ارفع مدير)$", msg):
        db.set_rank(gid, tid, "مدير")
        await event.respond(f"🎖️ تم رفع **{name}** ليكون **مديراً** في البوت.")
        
    elif re.match(r"^(رفع ادمن|ارفع ادمن)$", msg):
        db.set_rank(gid, tid, "ادمن")
        await event.respond(f"🛡️ تم رفع **{name}** ليكون **ادمناً** في البوت.")
        
    elif re.match(r"^(رفع مميز|ارفع مميز)$", msg):
        db.set_rank(gid, tid, "مميز")
        await event.respond(f"✨ تم رفع **{name}** ليكون **عضواً مميزاً**.")
        
    elif re.match(r"^(تنزيل|حذف رتبة)$", msg):
        db.set_rank(gid, tid, "عضو")
        await event.respond(f"👤 تم تنزيل **{name}** لرتبة **عضو**.")

# --- 2. أوامر العقوبات الإدارية (حظر، كتم، طرد) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def admin_actions_handler(event):
    msg = event.raw_text
    gid = event.chat_id
    
    if not event.is_reply: return
    if not await check_privilege(event, "ادمن"): return

    reply = await event.get_reply_message()
    tid = reply.sender_id
    
    # منع معاقبة المنشئ أو الإدمنية الأعلى
    if tid == OWNER_ID:
        await event.respond("❌ لا يمكنني تنفيذ عقوبة بحق منشئ البوت!")
        return

    # تنفيذ العمليات
    if msg == "حظر":
        await client.edit_permissions(gid, tid, view_messages=False)
        await event.respond("🚫 تم حظر العضو من المجموعة بنجاح.")
        
    elif msg == "طرد":
        await client.kick_participant(gid, tid)
        await event.respond("👞 تم طرد العضو من المجموعة.")
        
    elif msg == "كتم":
        await client.edit_permissions(gid, tid, send_messages=False)
        await event.respond("🔇 تم كتم العضو ومنعه من التحدث.")
        
    elif msg == "تقييد":
        # تقييد الميديا فقط (مثل تون)
        await client.edit_permissions(gid, tid, send_media=False, send_stickers=False, send_gifs=False)
        await event.respond("⚠️ تم تقييد العضو من إرسال الميديا.")

    elif msg in ["الغاء الحظر", "رفع الحظر"]:
        await client.edit_permissions(gid, tid, view_messages=True)
        await event.respond("✅ تم إلغاء حظر العضو.")

    elif msg in ["الغاء الكتم", "رفع الكتم"]:
        await client.edit_permissions(gid, tid, send_messages=True)
        await event.respond("🔊 تم إلغاء كتم العضو.")

# --- 3. أمر كشف المعلومات (بيانات العضو) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def info_handler(event):
    if event.raw_text == "كشف" and event.is_reply:
        reply = await event.get_reply_message()
        u = await reply.get_sender()
        rank = db.get_rank(str(event.chat_id), u.id)
        
        info = (
            f"🔍 **معلومات العضو:**\n"
            f"▫️ الاسم: {u.first_name}\n"
            f"▫️ الآيدي: `{u.id}`\n"
            f"▫️ اليوزر: @{u.username if u.username else 'لا يوجد'}\n"
            f"▫️ الرتبة: **{rank}**"
        )
        await event.respond(info)
