import asyncio
import re
from telethon import TelegramClient, events, Button, types
from database_handler import Database

# --- البيانات الأساسية ---
API_ID = '33183154'
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

db = Database()
client = TelegramClient('SuperAdmin', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- دالة التحقق من الرتب ---
async def get_user_rank(event):
    if event.sender_id == OWNER_ID: return "المنشئ"
    return db.get_rank(event.chat_id, event.sender_id)

# --- 1. التشغيل التلقائي (Automatic Handlers) لمنع الروابط والصور ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_cleaner(event):
    if await get_user_rank(event) in ["المنشئ", "مدير", "مميز"]: return

    gid = str(event.chat_id)
    
    # منع الروابط (Regex)
    if db.get_setting(gid, "links") == "close":
        if re.search(r'(https?://\S+|t\.me/\S+|@\S+)', event.raw_text):
            await event.delete()
            return

    # منع الصور
    if event.photo and db.get_setting(gid, "photos") == "close":
        await event.delete()

# --- 2. لوحة التحكم بالأزرار (Inline Keyboards) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS, pattern="^امر$"))
async def cmd_panel(event):
    buttons = [
        [Button.inline("🛡️ إعدادات الحماية", data="settings"), Button.inline("👥 الرتب", data="ranks")],
        [Button.inline("💬 الردود", data="replies"), Button.inline("👋 الترحيب", data="welcome")],
        [Button.url("📢 قناة السورس", "https://t.me/YourChannel")]
    ]
    await event.respond("⬇️ **أهلاً بك في لوحة تحكم البوت الذكية:**", buttons=buttons)

# --- 3. معالج أزرار لوحة التحكم ---
@client.on(events.CallbackQuery())
async def callback_handler(event):
    if not await get_user_rank(event) in ["المنشئ", "مدير"]:
        await event.answer("⚠️ عذراً، هذا الأمر للمدراء فقط!", alert=True)
        return

    data = event.data.decode('utf-8')
    if data == "settings":
        btns = [
            [Button.inline("قفل الروابط", data="lock_links"), Button.inline("فتح الروابط", data="unlock_links")],
            [Button.inline("قفل الصور", data="lock_photos"), Button.inline("فتح الصور", data="unlock_photos")],
            [Button.inline("🔙 رجوع", data="back")]
        ]
        await event.edit("🛠️ **إعدادات الحماية التلقائية:**", buttons=btns)
    
    elif data == "lock_links":
        db.set_setting(event.chat_id, "links", "close")
        await event.answer("🔒 تم قفل الروابط بنجاح", alert=True)

# --- 4. الأوامر الذكية (Regex) للإدارة بالرد ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def admin_tools(event):
    msg = event.raw_text
    if not event.is_reply: return
    rank = await get_user_rank(event)
    if rank not in ["المنشئ", "مدير"]: return

    reply = await event.get_reply_message()
    tid = reply.sender_id

    # استخدام Regex لدعم كلمات متعددة (ارفع، رفع، ترقية)
    if re.match(r"^(رفع مدير|ارفع مدير|ترقية مدير)$", msg):
        db.set_rank(event.chat_id, tid, "مدير")
        await event.respond(f"🎖️ تم رفع العضو كـ **مدير** في البوت.")

    elif re.match(r"^(كتم|اكتم)$", msg):
        await client.edit_permissions(event.chat_id, tid, send_messages=False)
        await event.respond("🔇 تم كتم العضو تلقائياً.")

# --- التشغيل ---
print("البوت الاحترافي يعمل الآن...")
client.run_until_disconnected()
