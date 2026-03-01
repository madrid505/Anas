import re
from telethon import events, types
from database import db
import main # استيراد ملف main للوصول للعميل والصلاحيات

@main.client.on(events.NewMessage(chats=main.ALLOWED_GROUPS))
async def extended_ranks_manager(event):
    msg = event.raw_text
    gid = str(event.chat_id)
    
    # جميع الأوامر في هذا الموديول تتطلب الرد على رسالة الشخص
    if not event.is_reply:
        return
    
    # --- أولاً: أوامر الرفع والتنزيل (صلاحية مالك فأعلى) ---
    if await main.check_privilege(event, "مالك"):
        reply_msg = await event.get_reply_message()
        target_id = str(reply_msg.sender_id)
        target_user = await reply_msg.get_sender()
        name = target_user.first_name if target_user else "العضو"

        # أوامر الرفع
        if msg in ["رفع مالك", "ارفع مالك"]:
            db.set_rank(gid, target_id, "مالك")
            await event.respond(f"👑 تم رفع **{name}** ليكون **مالكاً** في البوت.")
        
        elif msg in ["رفع مدير", "ارفع مدير"]:
            db.set_rank(gid, target_id, "مدير")
            await event.respond(f"🎖️ تم رفع **{name}** ليكون **مديراً** في البوت.")
            
        elif msg in ["رفع ادمن", "ارفع ادمن"]:
            db.set_rank(gid, target_id, "ادمن")
            await event.respond(f"🛡️ تم رفع **{name}** ليكون **ادمناً** في البوت.")
            
        elif msg in ["رفع مميز", "ارفع مميز"]:
            db.set_rank(gid, target_id, "مميز")
            await event.respond(f"✨ تم رفع **{name}** ليكون **عضواً مميزاً**.")
            
        # أوامر التنزيل
        elif msg in ["تنزيل", "حذف رتبة"]:
            db.set_rank(gid, target_id, "عضو")
            await event.respond(f"👤 تم تنزيل **{name}** وإلغاء رتبته إلى **عضو**.")

    # --- ثانياً: أوامر العقوبات الإدارية (صلاحية ادمن فأعلى) ---
    if await main.check_privilege(event, "ادمن"):
        reply_msg = await event.get_reply_message()
        target_id = reply_msg.sender_id
        
        # حماية منشئ البوت (OWNER_ID) من أي عقوبات
        if target_id == main.OWNER_ID:
            if msg in ["حظر", "كتم", "طرد", "تقييد"]:
                await event.respond("⚠️ لا يمكنني تنفيذ عقوبة بحق منشئ البوت (المالك الأساسي)!")
                return

        # تنفيذ عقوبة الحظر
        if msg == "حظر":
            try:
                await main.client.edit_permissions(event.chat_id, target_id, view_messages=False)
                await event.respond("🚫 تم **حظر** العضو من المجموعة بنجاح.")
            except Exception as e:
                await event.respond(f"❌ فشل الحظر: تأكد أن البوت لديه صلاحيات إدمن.")
            
        # تنفيذ عقوبة الطرد
        elif msg == "طرد":
            try:
                await main.client.kick_participant(event.chat_id, target_id)
                await event.respond("👞 تم **طرد** العضو من المجموعة.")
            except Exception as e:
                await event.respond(f"❌ فشل الطرد.")
            
        # تنفيذ عقوبة الكتم
        elif msg == "كتم":
            try:
                await main.client.edit_permissions(event.chat_id, target_id, send_messages=False)
                await event.respond("🔇 تم **كتم** العضو بنجاح (منعه من إرسال الرسائل).")
            except Exception as e:
                await event.respond(f"❌ فشل الكتم.")
            
        # تنفيذ عقوبة التقييد (منع الوسائط فقط)
        elif msg == "تقييد":
            try:
                await main.client.edit_permissions(event.chat_id, target_id, send_media=False, send_stickers=False, send_gifs=False, send_games=False, send_inline=False)
                await event.respond("⚠️ تم **تقييد** العضو من إرسال الوسائط والملصقات.")
            except Exception as e:
                await event.respond(f"❌ فشل التقييد.")

        # إلغاء العقوبات (رفع الحظر / رفع الكتم)
        elif msg in ["الغاء الحظر", "رفع الحظر"]:
            await main.client.edit_permissions(event.chat_id, target_id, view_messages=True, send_messages=True, send_media=True, send_stickers=True, send_gifs=True)
            await event.respond("✅ تم **رفع الحظر** عن العضو ويمكنه الدخول الآن.")

        elif msg in ["الغاء الكتم", "رفع الكتم", "الغاء التقييد"]:
            await main.client.edit_permissions(event.chat_id, target_id, send_messages=True, send_media=True, send_stickers=True, send_gifs=True)
            await event.respond("🔊 تم **رفع الكتم/التقييد** عن العضو بنجاح.")

    # --- ثالثاً: أمر كشف المعلومات الشخصية ---
    if msg == "كشف":
        reply_msg = await event.get_reply_message()
        target_user = await reply_msg.get_sender()
        user_rank_in_db = db.get_rank(gid, target_user.id)
        
        info_message = (
            f"🔍 **بطاقة معلومات العضو:**\n"
            f"━━━━━━━━━━━━━━\n"
            f"▫️ الاسم: {target_user.first_name}\n"
            f"▫️ الآيدي: `{target_user.id}`\n"
            f"▫️ المعرف: @{target_user.username if target_user.username else 'لا يوجد'}\n"
            f"▫️ الرتبة: **{user_rank_in_db}**\n"
            f"━━━━━━━━━━━━━━"
        )
        await event.respond(info_message)
