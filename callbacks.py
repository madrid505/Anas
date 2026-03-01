from telethon import events, Button
from main import client
from database import db

@client.on(events.CallbackQuery())
async def handle_buttons(event):
    data = event.data.decode('utf-8')
    gid = str(event.chat_id)

    if data == "lock_links":
        db.toggle_lock(gid, "links", 1)
        await event.answer("🔒 تم قفل الروابط", alert=True)
    
    elif data == "unlock_links":
        db.toggle_lock(gid, "links", 0)
        await event.answer("🔓 تم فتح الروابط", alert=True)

    elif data == "close_menu":
        await event.delete()
