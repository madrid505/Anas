import re
from telethon import events, types
from database import db
# الاستيراد الصحيح لمنع تعليق قاعدة البيانات
from __main__ import client, OWNER_ID, ALLOWED_GROUPS, check_privilege 

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def ranks_manager_system(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # كافة أوامر هذا الملف تتطلب الرد على رسالة العضو المستهدف
    if not event.is_reply:
        return
    
    # جلب بيانات الشخص المردود عليه
    reply_msg = await event.get_reply_message()
    target_id = reply_msg.sender_id
    target_st_id = str(target_id)
    
    # جلب معلومات المستخدم (الاسم) لضمان التفاعل الشخصي
    target_user = await reply_msg.get_sender()
    name = target_user.first_name if target_user else "العضو"

    # --- 1. أوامر الرفع والتنزيل (صلاحية مالك فأعلى) ---
    if await check_privilege(event, "مالك"):
        
        if msg in ["رفع مالك", "ارفع مالك"]:
            db.set_rank(gid, target_st_id, "مالك")
            await event.respond(f"👑 تم رفع **{name}** ليكون **مالكاً** في البوت.")
            return

        elif msg in ["رفع مدير", "ارفع مدير"]:
            db.set_rank(gid, target_st_id, "مدير")
            await event.respond(f"🎖️ تم رفع **{name}** ليكون **مديراً** في البوت.")
            return

        elif msg in ["رفع ادمن", "ارفع ادمن"]:
            db.set_rank(gid, target_st_id, "ادمن")
            await event.respond(f"🛡️ تم رفع **{name}** ليكون **ادمناً** في البوت.")
            return

        elif msg in ["رفع مميز", "ارفع مميز"]:
            db.set_rank(gid, target_st_id, "مميز")
            await event.respond(f"✨ تم رفع **{name}** ليكون **عضواً مميزاً**.")
            return

        elif msg in ["تنزيل", "حذف رتبة"]:
            db.set_rank(gid, target_st_id, "عضو")
            await event.respond(f"👤 تم تنزيل **{name}** وإلغاء كافة رتبه.")
            return

    # --- 2. أوامر العقوبات الإدارية (صلاحية ادمن فأعلى) ---
    if await check_privilege(event, "ادمن"):
        
        # حماية منشئ البوت (أنت يا أنس) من أي عقوبة بالخطأ
        if target_id == OWNER_ID:
            if msg in ["حظر", "كتم", "طرد", "تقييد"]:
                await event.respond("⚠️ خطأ ملكي: لا يمكن تنفيذ عقوبة بحق منشئ البوت!")
                return

        # تنفيذ الحظر الكامل للمجموعة
        if msg == "حظر":
            try:
                await client.edit_permissions(event.chat_id, target_id, view_messages=False)
                await event.respond(f"🚫 تم حظر **{name}** من المجموعة بنجاح.")
            except Exception:
                await event.respond("❌ فشل الحظر: تأكد من صلاحيات البوت الإدارية.")

        # تنفيذ الطرد الفوري
        elif msg == "طرد":
            try:
                await client.kick_participant(event.chat_id, target_id)
                await event.respond(f"👞 تم طرد **{name}** من المجموعة بنجاح.")
            except Exception:
                await event.respond("❌ فشل الطرد: قد يكون العضو مديراً أو بوت.")

        # تنفيذ الكتم (منع إرسال الرسائل)
        elif msg == "كتم":
            try:
                await client.edit_permissions(event.chat_id, target_id, send_messages=False)
                await event.respond(f"🔇 تم كتم **{name}** بنجاح.")
            except Exception:
                await event.respond("❌ فشل الكتم: تأكد من الصلاحيات.")

        # تنفيذ التقييد (منع إرسال الميديا فقط)
        elif msg == "تقييد":
            try:
                await client.edit_permissions(event.chat_id, target_id, send_media=False, send_stickers=False, send_gifs=False)
                await event.respond(f"⚠️ تم تقييد **{name}** من إرسال الوسائط.")
            except Exception:
                await event.respond("❌ فشل التقييد.")

        # إلغاء العقوبات (رفع الحظر)
        elif msg in ["الغاء الحظر", "رفع الحظر"]:
            try:
                await client.edit_permissions(event.chat_id, target_id, view_messages=True, send_messages=True)
                await event.respond(f"✅ تم إلغاء حظر **{name}** ويمكنه العودة الآن.")
            except Exception: pass

        # إلغاء الكتم والتقييد
        elif msg in ["الغاء الكتم", "رفع الكتم", "الغاء التقييد"]:
            try:
                await client.edit_permissions(event.chat_id, target_id, send_messages=True, send_media=True, send_stickers=True)
                await event.respond(f"🔊 تم إلغاء كتم/تقييد **{name}** بنجاح.")
            except Exception: pass

    # --- 3. أمر كشف المعلومات (متاح للجميع لضمان الشفافية) ---
    if msg == "كشف":
        user_rank = db.get_rank(gid, target_id)
        info = (
            f"🔍 **بطاقة معلومات العضو الملكية:**\n"
            f"━━━━━━━━━━━━━━\n"
            f"▫️ الاسم: {name}\n"
            f"▫️ الآيدي: `{target_id}`\n"
            f"▫️ الرتبة: **{user_rank}**\n"
            f"🛡️ الحالة: عضو مسجل في Monopoly\n"
            f"━━━━━━━━━━━━━━"
        )
        await event.respond(info)
