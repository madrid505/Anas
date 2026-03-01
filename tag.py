import asyncio
from telethon import events
from database import db
import main  # الوصول للعميل والصلاحيات والمجموعات المسموحة

# قاموس لتتبع عمليات التاغ الجارية لإمكانية إيقافها
active_tagging = {}

@main.client.on(events.NewMessage(chats=main.ALLOWED_GROUPS))
async def tag_handler(event):
    msg = event.raw_text
    chat_id = event.chat_id
    gid = str(chat_id)

    # التحقق من الصلاحية (يجب أن يكون مدير فأعلى لاستخدام التاغ)
    if not await main.check_privilege(event, "مدير"):
        return

    # --- 1. أمر بدء المنشن (تاغ للكل) ---
    if msg in ["تاغ", "منشن", "تاق"]:
        # إذا كانت هناك عملية منشن جارية، نمنع البدء بجديدة
        if gid in active_tagging and active_tagging[gid]:
            await event.respond("⚠️ هناك عملية **تاغ** جارية بالفعل!")
            return

        active_tagging[gid] = True
        await event.respond("📣 جاري بدء **المنشن الشامل** لجميع الأعضاء...")

        # جلب قائمة الأعضاء
        members = await main.client.get_participants(chat_id)
        
        # تقسيم الأعضاء لمجموعات (مثلاً 5 أعضاء في كل رسالة لتجنب السبام)
        chunk_size = 5
        for i in range(0, len(members), chunk_size):
            # التحقق إذا قام الإدمن بإيقاف التاغ أثناء العملية
            if not active_tagging.get(gid, False):
                break
            
            chunk = members[i:i + chunk_size]
            tag_msg = ""
            for user in chunk:
                if not user.bot: # استثناء البوتات من المنشن
                    tag_msg += f"[{user.first_name}](tg://user?id={user.id})  "
            
            if tag_msg:
                await main.client.send_message(chat_id, tag_msg)
                # تأخير بسيط لتجنب حظر البوت من التليجرام (Flood Wait)
                await asyncio.sleep(2)

        if active_tagging.get(gid):
            await event.respond("✅ تم اكتمال **المنشن الشامل** لجميع الأعضاء.")
            active_tagging[gid] = False

    # --- 2. أمر إيقاف المنشن ---
    elif msg in ["ايقاف التاغ", "ايقاف المنشن", "وقف التاغ"]:
        if gid in active_tagging and active_tagging[gid]:
            active_tagging[gid] = False
            await event.respond("🛑 تم **إيقاف** عملية المنشن بنجاح.")
        else:
            await event.respond("❌ لا توجد عملية **تاغ** جارية حالياً.")

    # --- 3. أمر منشن للمدراء فقط ---
    elif msg in ["تاغ للمدراء", "منشن للمدراء"]:
        await event.respond("📢 جاري منشن **طاقم الإدارة**...")
        admins = await main.client.get_participants(chat_id, filter=events.types.ChannelParticipantsAdmins())
        
        admin_tags = "👮‍♂️ **قائمة المدراء:**\n\n"
        for admin in admins:
            if not admin.bot:
                admin_tags += f"▫️ [{admin.first_name}](tg://user?id={admin.id})\n"
        
        await main.client.send_message(chat_id, admin_tags)
