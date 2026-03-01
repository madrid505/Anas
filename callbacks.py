from telethon import events, Button
from database import db
import main  # الوصول لـ client و check_privilege

# --- معالج الضغط على الأزرار (Callback Queries) ---
@main.client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    gid = str(event.chat_id)
    
    # 1. التحقق من الصلاحية (يسمح فقط للمدير فأعلى بالتحكم بالأزرار)
    if not await main.check_privilege(event, "مدير"):
        await event.answer("⚠️ عذراً، هذه اللوحة مخصصة للمدراء فقط!", alert=True)
        return

    # --- القائمة الرئيسية ---
    if data == "show_main":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.edit("⬇️ **لوحة تحكم بوت الأساطير (نظام TON):**", buttons=btns)

    # --- قائمة الحماية (الأقفال) ---
    elif data == "show_locks":
        # عرض حالة الأقفال الحالية بجانب كل زر
        def get_stat(feat): return "🔒" if db.is_locked(gid, feat) else "🔓"
        
        btns = [
            [Button.inline(f"{get_stat('links')} الروابط", "toggle_links"), Button.inline(f"{get_stat('usernames')} المعرفات", "toggle_usernames")],
            [Button.inline(f"{get_stat('photos')} الصور", "toggle_photos"), Button.inline(f"{get_stat('stickers')} الملصقات", "toggle_stickers")],
            [Button.inline(f"{get_stat('forward')} التوجيه", "toggle_forward"), Button.inline(f"{get_stat('videos')} الفيديوهات", "toggle_videos")],
            [Button.inline("⬅️ رجوع", "show_main")]
        ]
        await event.edit("🔐 **إعدادات الحماية والأقفال:**\n(اضغط على الزر لتغيير الحالة)", buttons=btns)

    # --- منطق تبديل الأقفال (Toggle) ---
    elif data.startswith("toggle_"):
        feature = data.replace("toggle_", "")
        current_status = db.is_locked(gid, feature)
        new_status = 0 if current_status else 1
        db.toggle_lock(gid, feature, new_status)
        # تحديث القائمة فوراً لإظهار التغيير
        await callback_handler(event) # إعادة استدعاء الدالة لتحديث الأزرار

    # --- قائمة الرتب (عرض توضيحي) ---
    elif data == "show_ranks":
        ranks_info = (
            "🎖️ **نظام الرتب في البوت:**\n"
            "━━━━━━━━━━━━━━\n"
            "👑 **المالك:** صلاحيات كاملة + رفع المدراء.\n"
            "🎖️ **المدير:** التحكم بالأقفال والطرد والمنشن.\n"
            "🛡️ **الادمن:** الحظر والكتم والتقييد.\n"
            "✨ **المميز:** تخطي كافة أقفال الحماية.\n"
            "━━━━━━━━━━━━━━"
        )
        await event.edit(ranks_info, buttons=[[Button.inline("⬅️ رجوع", "show_main")]])

    # --- قائمة الإعدادات ---
    elif data == "show_settings":
        w_stat = "✅ مفعل" if db.get_setting(gid, "welcome_status") == "on" else "❌ معطل"
        btns = [
            [Button.inline(f"الترحيب: {w_stat}", "toggle_welcome")],
            [Button.inline("⬅️ رجوع", "show_main")]
        ]
        await event.edit("⚙️ **إعدادات البوت العامة:**", buttons=btns)

    # --- تبديل حالة الترحيب ---
    elif data == "toggle_welcome":
        current = db.get_setting(gid, "welcome_status")
        new_val = "off" if current == "on" else "on"
        db.set_setting(gid, "welcome_status", new_val)
        await callback_handler(event)

    # --- إغلاق اللوحة ---
    elif data == "close":
        await event.delete()
