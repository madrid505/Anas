from main import client, events, Button
from database import db

@client.on(events.CallbackQuery())
async def callback_manager(event):
    data = event.data
    gid = str(event.chat_id)

    if data == b"show_locks":
        btns = [
            [Button.inline("الروابط: " + ("🔒" if db.is_locked(gid, "links") else "🔓"), b"tgl_links")],
            [Button.inline("الصور: " + ("🔒" if db.is_locked(gid, "photos") else "🔓"), b"tgl_photos")],
            [Button.inline("🔙 رجوع", b"back_to_main")]
        ]
        await event.edit("🛠️ **تحكم بأقفال المجموعة:**", buttons=btns)

    elif data == b"tgl_links":
        new_status = 0 if db.is_locked(gid, "links") else 1
        db.toggle_lock(gid, "links", new_status)
        await event.answer("✅ تم تحديث قفل الروابط", alert=False)
        # تحديث الأزرار فوراً
        await callback_manager.as_event(event) 

    elif data == b"close_menu":
        await event.delete()
