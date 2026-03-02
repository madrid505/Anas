from telethon import events, Button
from database import db
# التعديل الجوهري لمنع تكرار فتح الجلسة وتعليق القاعدة
from __main__ import client, check_privilege 

@client.on(events.CallbackQuery)
async def callback_handler(event):
    # تحويل البيانات القادمة من الزر إلى نص
    data = event.data.decode('utf-8')
    gid = str(event.chat_id)
    
    # 1. التحقق من الصلاحية (يسمح فقط للمدير فأعلى بالتحكم بالأزرار)
    if not await check_privilege(event, "مدير"):
        await event.answer("⚠️ عذراً، هذه اللوحة مخصصة للمدراء فقط!", alert=True)
        return

    # --- القائمة الرئيسية (Main Menu) ---
    if data == "show_main":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("📜 الأوامر", "show_cmds"), Button.inline("⚙️ الإعدادات", "show_settings")],
            [Button.inline("❌ إغلاق", "close")]
        ]
        await event.edit("♥️ Monopoly مونوبولي لوحة تحكم ♥️", buttons=btns)

    # --- قائمة الأوامر (المحدثة بجميع أوامر الردود) ---
    elif data == "show_cmds":
        cmds_text = (
            "📜 **دليل أوامر Monopoly للمشرفين:**\n"
            "━━━━━━━━━━━━━━\n"
            "📌 **أوامر الإدارة (بالرد):**\n"
            "• `تثبيت` : لتثبيت الرسالة.\n"
            "• `حذف` : لحذف رسالة العضو.\n"
            "• `طرد` : لطرد العضو من المجموعة.\n"
            "• `كشف` : لإظهار بطاقة بيانات العضو.\n\n"
            "⚙️ **أوامر النظام والردود:**\n"
            "• `اضف رد` : لإضافة رد ذكي (نص/ميديا).\n"
            "• `حذف رد` : لحذف رد مبرمج معين.\n"
            "• `مسح الردود` : حذف جميع الردود المضافة.\n"
            "• `المتفاعلين` : لعرض قائمة توب 5.\n"
            "• `امر` : لفتح هذه اللوحة.\n"
            "━━━━━━━━━━━━━━"
        )
        await event.edit(cmds_text, buttons=[[Button.inline("⬅️ رجوع", "show_main")]])

    # --- قائمة الحماية والأقفال (Locks Menu) ---
    elif data == "show_locks":
        # وظيفة داخلية لجلب حالة القفل (قفل/فتح)
        links_s = "🔒" if db.is_locked(gid, "links") else "🔓"
        users_s = "🔒" if db.is_locked(gid, "usernames") else "🔓"
        photo_s = "🔒" if db.is_locked(gid, "photos") else "🔓"
        stick_s = "🔒" if db.is_locked(gid, "stickers") else "🔓"
        forw_s = "🔒" if db.is_locked(gid, "forward") else "🔓"
        video_s = "🔒" if db.is_locked(gid, "videos") else "🔓"
        
        btns = [
            [Button.inline(f"{links_s} الروابط", "tg_links"), Button.inline(f"{users_s} المعرفات", "tg_usernames")],
            [Button.inline(f"{photo_s} الصور", "tg_photos"), Button.inline(f"{stick_s} الملصقات", "tg_stickers")],
            [Button.inline(f"{forw_s} التوجيه", "tg_forward"), Button.inline(f"{video_s} الفيديوهات", "tg_videos")],
            [Button.inline("⬅️ رجوع", "show_main")]
        ]
        await event.edit("🔐 **إعدادات الحماية والأقفال:**\n(اضغط على الزر لتغيير الحالة مباشرة)", buttons=btns)

    # --- منطق تبديل الأقفال (Toggle Logic) ---
    elif data.startswith("tg_"):
        feature = data.replace("tg_", "")
        
        # إذا كان الزر خاص بالترحيب
        if feature == "welcome":
            curr_w = db.get_setting(gid, "welcome_status")
            new_w = "off" if curr_w == "on" else "on"
            db.set_setting(gid, "welcome_status", new_w)
            # تحديث قائمة الإعدادات فوراً
            w_stat = "✅ مفعل" if new_w == "on" else "❌ معطل"
            btns_w = [[Button.inline(f"نظام الترحيب: {w_stat}", "tg_welcome")], [Button.inline("⬅️ رجوع", "show_main")]]
            await event.edit("⚙️ **إعدادات البوت العامة:**", buttons=btns_w)
        
        # إذا كان الزر خاص بالأقفال ميديا/روابط
        else:
            current_l = db.is_locked(gid, feature)
            db.toggle_lock(gid, feature, 0 if current_l else 1)
            # تحديث قائمة الأقفال فوراً لإظهار الرموز الجديدة
            l_s = "🔒" if db.is_locked(gid, "links") else "🔓"
            u_s = "🔒" if db.is_locked(gid, "usernames") else "🔓"
            p_s = "🔒" if db.is_locked(gid, "photos") else "🔓"
            s_s = "🔒" if db.is_locked(gid, "stickers") else "🔓"
            f_s = "🔒" if db.is_locked(gid, "forward") else "🔓"
            v_s = "🔒" if db.is_locked(gid, "videos") else "🔓"
            
            btns_l = [
                [Button.inline(f"{l_s} الروابط", "tg_links"), Button.inline(f"{u_s} المعرفات", "tg_usernames")],
                [Button.inline(f"{p_s} الصور", "tg_photos"), Button.inline(f"{s_s} الملصقات", "tg_stickers")],
                [Button.inline(f"{f_s} التوجيه", "tg_forward"), Button.inline(f"{v_s} الفيديوهات", "tg_videos")],
                [Button.inline("⬅️ رجوع", "show_main")]
            ]
            await event.edit("🔐 **إعدادات الحماية والأقفال:**", buttons=btns_l)

    # --- قائمة معلومات الرتب ---
    elif data == "show_ranks":
        ranks_text = (
            "🎖️ **نظام الرتب والصلاحيات:**\n"
            "━━━━━━━━━━━━━━\n"
            "👑 **المالك:** تحكم مطلق في كل شيء.\n"
            "🎖️ **المدير:** تحكم بالأقفال والترحيب والمنشن.\n"
            "🛡️ **الادمن:** صلاحيات الحظر والكتم والطرد.\n"
            "✨ **المميز:** لا يتأثر بأقفال الحماية (صور، روابط..).\n"
            "━━━━━━━━━━━━━━"
        )
        await event.edit(ranks_text, buttons=[[Button.inline("⬅️ رجوع", "show_main")]])

    # --- قائمة الإعدادات العامة ---
    elif data == "show_settings":
        current_welcome = db.get_setting(gid, "welcome_status")
        w_label = "✅ مفعل" if current_welcome == "on" else "❌ معطل"
        btns_s = [
            [Button.inline(f"نظام الترحيب: {w_label}", "tg_welcome")],
            [Button.inline("⬅️ رجوع", "show_main")]
        ]
        await event.edit("⚙️ **إعدادات البوت العامة:**", buttons=btns_s)

    # --- إغلاق اللوحة وحذف الرسالة ---
    elif data == "close":
        await event.delete()
