import asyncio
import sqlite3
import logging
from telethon import TelegramClient, events, functions, types
from telethon.tl.types import ChannelParticipantsAdmins

# --- الإعدادات (تم دمج بياناتك) ---
API_ID = '25736711' # يمكنك تحديثه من my.telegram.org إذا لزم
API_HASH = '809081e792461f52b8265a73e13d5b00'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

logging.basicConfig(level=logging.INFO)
client = TelegramClient('SuperBot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- إعداد قاعدة البيانات ---
db = sqlite3.connect('bot_database.db')
cursor = db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS users (uid TEXT, name TEXT, username TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS warns (uid TEXT, gid TEXT, count INTEGER DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, feature TEXT, status TEXT DEFAULT "open")')
db.commit()

# --- دوال التحقق ---
async def check_admin(event):
    if event.sender_id == OWNER_ID: return True
    if event.chat_id not in ALLOWED_GROUPS: return False
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    return perms.is_admin or perms.is_creator

# --- مراقب تغيير الأسماء ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def identity_monitor(event):
    user = await event.get_sender()
    if not user or not isinstance(user, types.User): return
    uid, cur_name = str(user.id), f"{user.first_name or ''} {user.last_name or ''}".strip()
    cur_un = f"@{user.username}" if user.username else "لا يوجد"
    
    cursor.execute("SELECT name, username FROM users WHERE uid=?", (uid,))
    row = cursor.fetchone()
    if row:
        old_n, old_un = row
        if old_n != cur_name or old_un != cur_un:
            await event.respond(f"🔍 **تنبيه تغيير بيانات:**\n👤 القديم: {old_n} ({old_un})\n✅ الجديد: {cur_name} ({cur_un})\n🆔 ID: `{uid}`")
            cursor.execute("UPDATE users SET name=?, username=? WHERE uid=?", (cur_name, cur_un, uid))
    else:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (uid, cur_name, cur_un))
    db.commit()

# --- معالج الأوامر العربية ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def manager(event):
    msg = event.raw_text
    chat_id = str(event.chat_id)
    
    # الردود التلقائية
    cursor.execute("SELECT reply FROM replies WHERE gid=? AND word=?", (chat_id, msg))
    rep = cursor.fetchone()
    if rep: await event.respond(rep[0])

    if not await check_admin(event): return

    # أوامر الإدارة بالرد
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        target_id = reply_msg.sender_id
        
        if msg == "طرد":
            await client.kick_participant(event.chat_id, target_id)
            await event.respond("✅ تم الطرد")
        elif msg == "حظر":
            await client.edit_permissions(event.chat_id, target_id, view_messages=False)
            await event.respond("🚫 تم الحظر")
        elif msg == "كتم":
            await client.edit_permissions(event.chat_id, target_id, send_messages=False)
            await event.respond("🔇 تم الكتم")
        elif msg == "تقييد":
            await client.edit_permissions(event.chat_id, target_id, send_messages=False, send_media=False)
            await event.respond("⚠️ تم التقييد")
        elif msg in ["الغاء الحظر", "الغاء الطرد", "الغاء الكتم", "الغاء التقييد", "رفع القيود"]:
            await client.edit_permissions(event.chat_id, target_id, view_messages=True, send_messages=True, send_media=True)
            await event.respond("✅ تم رفع القيود")
        elif msg == "تثبيت":
            await client.pin_from_id(event.chat_id, reply_msg.id)
            await event.respond("📌 تم التثبيت")
        elif msg == "كشف":
            u = await client.get_entity(target_id)
            await event.respond(f"🆔 ID: `{u.id}`\n👤 الاسم: {u.first_name}\n🔗 اليوزر: @{u.username}")

    # أوامر عامة
    if msg == "تاك":
        users = await client.get_participants(event.chat_id)
        mentions = [f"[\u2063](tg://user?id={u.id})" for u in users if not u.bot]
        for i in range(0, len(mentions), 5):
            await event.respond("📣 منشن عام: " + "".join(mentions[i:i+5]))
            await asyncio.sleep(1)
    
    elif msg.startswith("اضف رد "):
        _, word, r = msg.split(" ", 2)
        cursor.execute("INSERT INTO replies VALUES (?, ?, ?)", (chat_id, word, r))
        db.commit()
        await event.respond(f"✅ تم حفظ الرد لـ: {word}")

    elif msg == "قفل الروابط":
        cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, 'links', 'close')", (chat_id,))
        db.commit()
        await event.respond("🔒 تم قفل الروابط")

# --- تشغيل ---
print("البوت يعمل بنجاح...")
client.run_until_disconnected()
