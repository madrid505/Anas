from telethon import events, Button
from main import client, check_privilege
from database import db

# دالة لتوليد أزرار الأقفال بشكل ديناميكي (مثل تون)
def get_locks_buttons(gid):
    features = [
        ("الروابط", "links"), ("الصور", "photos"),
        ("الملصقات", "stickers"), ("المتحركة", "gifs"),
        ("التوجيه", "forward"), ("المعرفات", "usernames")
    ]
    buttons = []
    # صنع صفوف من زرين لكل صف
    for i in range(0, len(features), 2):
        row = []
        for name, key in features[i:i+2]:
            status = "🔒" if db.is_locked(gid, key) else "🔓"
            row.append(Button.inline(f"{name} {status}", data=f"tgl_{key}"))
        buttons.append(row)
    
    buttons.append([Button.inline("🔙 رجوع", data="back_main")])
    return buttons

@client.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8')
    gid = str(event.chat_id)

    # التحقق من أن الشخص الذي ضغط الزر هو إدمن
    if not await check_privilege(event, "مدير"):
        await event.answer("⚠️ عذراً، هذه اللوحة للمدراء فقط!", alert=True)
        return

    # --- التنقل في القائمة الرئيسية ---
    if data == "show_locks":
        await event.edit("🔐 **قائمة التحكم بالأقفال:**\nاضغط على الزر للتبديل بين القفل والفتح.", 
                         buttons=get_locks_buttons(gid))

    elif data == "back_main":
        btns = [
            [Button.inline("🔒 الحماية", "show_locks"), Button.inline("🎖️ الرتب", "show_ranks")],
            [Button.inline("⚙️ الإعدادات", "show_settings"), Button.inline("❌ إغلاق", "close")]
        ]
        await event.edit("⬇️ **لوحة تحكم بوت الأساطير (نظام TON):**", buttons=btns)

    elif data == "close":
        await event.delete()

    # --- منطق التبديل التلقائي (Toggle Logic) ---
    elif data.startswith("tgl_"):
        feature = data.replace("tgl_", "")
        # عكس الحالة الحالية
        current_status = 1 if db.is_locked(gid, feature) else 0
        new_status = 0 if current_status == 1 else 1
        
        db.toggle_lock(gid, feature, new_status)
        
        # تحديث الرسالة فوراً بالأزرار الجديدة (تغيير القفل من 🔓 إلى 🔒)
        await event.edit(buttons=get_locks_buttons(gid))
        status_text = "تم القفل 🔒" if new_status == 1 else "تم الفتح 🔓"
        await event.answer(f"✅ {status_text}", alert=False)

    # --- عرض الرتب (نظام معلوماتي) ---
    elif data == "show_ranks":
        await event.answer("🎖️ نظام الرتب يعمل عبر الأوامر النصية (رفع/تنزيل).", alert=True)

    # --- الإعدادات (ترحيب، ردود) ---
    elif data == "show_settings":
        w_stat = "مفعل ✅" if db.get_setting(gid, "welcome_status") == "on" else "معطل ❌"
        btns = [
            [Button.inline(f"الترحيب: {w_stat}", data="tgl_welcome")],
            [Button.inline("🔙 رجوع", data="back_main")]
        ]
        await event.edit("⚙️ **إعدادات البوت العامة:**", buttons=btns)

    elif data == "tgl_welcome":
        current = db.get_setting(gid, "welcome_status")
        new = "off" if current == "on" else "on"
        db.set_setting(gid, "welcome_status", new)
        await callback_handler.as_event(event) # تحديث القائمة
