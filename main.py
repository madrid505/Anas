import asyncio
import logging
from telethon import TelegramClient, events, types
from database_handler import Database

# --- البيانات الخاصة بك ---
API_ID = '25736711'
API_HASH = '809081e792461f52b8265a73e13d5b00'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = Database()
client = TelegramClient('SuperAdminBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_admin(event):
    if event.sender_id == OWNER_ID: return True
    if event.chat_id not in ALLOWED_GROUPS: return False
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    return perms.is_admin or perms.is_creator

# --- نظام الترحيب التلقائي ---
@client.on(events.ChatAction)
async def welcome_handler(event):
    if event.user_joined or event.user_added:
        welcome_msg = db.get_welcome(event.chat_id)
        if welcome_msg:
            user = await event.get_user()
            final_msg = welcome_msg.replace("الاسم", user.first_name).replace("الاي دي", str(user.id))
            await event.respond(final_msg)

# --- نظام مراقبة تغيير الهوية ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def identity_check(event):
    user = await event.get_sender()
    if not user or not isinstance(user, types.User): return
    uid, name = str(user.id), f"{user.first_name or ''} {user.last_name or ''}".strip()
    un = f"@{user.username}" if user.username else "لا يوجد"
    
    db.cursor.execute("SELECT name, username FROM users WHERE uid=?", (uid,))
    row = db.cursor.fetchone()
    if row and (row[0] != name or row[1] != un):
        await event.respond(f"🔍 **تغيير بيانات:**\n👤 من: {row[0]} ({row[1]})\n✅ إلى: {name} ({un})\n🆔: `{uid}`")
        db.cursor.execute("UPDATE users SET name=?, username=? WHERE uid=?", (name, un, uid))
    elif not row:
        db.cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (uid, name, un))
    db.conn.commit()

# --- معالج الأوامر العربية الشامل ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def main_controller(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # ردود تلقائية
    db.cursor.execute("SELECT reply FROM replies WHERE gid=? AND word=?", (gid, msg))
    res = db.cursor.fetchone()
    if res: await event.respond(res[0])

    if not await is_admin(event): return

    # أوامر الإدارة بالرد
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        tid = reply_msg.sender_id
        
        if msg == "طرد": await client.kick_participant(event.chat_id, tid); await event.respond("✅ تم الطرد")
        elif msg == "حظر": await client.edit_permissions(event.chat_id, tid, view_messages=False); await event.respond("🚫 تم الحظر")
        elif msg == "كتم": await client.edit_permissions(event.chat_id, tid, send_messages=False); await event.respond("🔇 تم الكتم")
        elif msg == "تقييد": await client.edit_permissions(event.chat_id, tid, send_messages=False, send_media=False); await event.respond("⚠️ تم التقييد")
        elif msg in ["الغاء الحظر", "الغاء الكتم", "رفع القيود"]: 
            await client.edit_permissions(event.chat_id, tid, view_messages=True, send_messages=True, send_media=True)
            await event.respond("✅ تم رفع القيود")
        elif msg == "تثبيت": await client.pin_from_id(event.chat_id, reply_msg.id); await event.respond("📌 تم التثبيت")
        elif msg == "انذار":
            db.cursor.execute("UPDATE warns SET count = count + 1 WHERE uid=? AND gid=?", (str(tid), gid))
            # منطق الإنذارات هنا...
            await event.respond("⚠️ تم تسجيل إنذار للعضو")

    # أوامر الإعدادات
    if msg.startswith("اضف ترحيب "):
        txt = msg.replace("اضف ترحيب ", "")
        db.set_welcome(gid, txt)
        await event.respond("✅ تم حفظ رسالة الترحيب")
    
    elif msg == "تاك":
        users = await client.get_participants(event.chat_id)
        mentions = [f"[\u2063](tg://user?id={u.id})" for u in users if not u.bot]
        for i in range(0, len(mentions), 5):
            await event.respond("📣 منشن للجميع: " + "".join(mentions[i:i+5]))
            await asyncio.sleep(1)

    elif msg == "قفل الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=False)
        await event.respond("🔒 تم قفل الدردشة للجميع")

    elif msg == "فتح الدردشة":
        await client.edit_permissions(event.chat_id, send_messages=True)
        await event.respond("🔓 تم فتح الدردشة للجميع")

# --- التشغيل ---
print("البوت يعمل بنجاح...")
client.run_until_disconnected()
