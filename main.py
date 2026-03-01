import re
from telethon import TelegramClient, events, Button
from database import db

# بياناتك المعتمدة
API_ID = '33183154'
API_HASH = 'ccb195afa05973cf544600ad3c313b84'
BOT_TOKEN = '8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ'
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]

client = TelegramClient('TonClone', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دالة التحقق من الصلاحيات (نفس نظام تون)
async def check_privilege(event, required_rank):
    if event.sender_id == OWNER_ID: return True
    user_rank = db.get_rank(event.chat_id, event.sender_id)
    ranks_order = {"عضو": 0, "مميز": 1, "ادمن": 2, "مدير": 3, "مالك": 4, "المنشئ": 5}
    return ranks_order.get(user_rank, 0) >= ranks_order.get(required_rank, 0)

# --- أوامر الإدارة الذكية (Regex) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def admin_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # فتح قائمة الأوامر (امر)
    if msg == "امر":
        btns = [
            [Button.inline("🔒 الأقفال", b"show_locks"), Button.inline("🎖️ الرتب", b"show_ranks")],
            [Button.inline("⚙️ الإعدادات", b"show_settings"), Button.inline("🧹 التنظيف", b"show_clean")],
            [Button.inline("❌ إغلاق القائمة", b"close_menu")]
        ]
        await event.respond("⬇️ **لوحة تحكم الإدارة (نسخة TON):**", buttons=btns)

    # نظام الرفع والتنزيل (Regex)
    if event.is_reply:
        reply = await event.get_reply_message()
        uid = str(reply.sender_id)
        
        if re.match(r"^(رفع مدير|ارفع مدير)$", msg) and await check_privilege(event, "مالك"):
            db.set_rank(gid, uid, "مدير")
            await event.respond("🎖️ تم رفع العضو **مديراً** في البوت")
            
        elif re.match(r"^(تنزيل|طرد)$", msg) and await check_privilege(event, "ادمن"):
            # تنفيذ الطرد أو تنزيل الرتبة
            pass

# --- نظام الحماية التلقائي (Automatic Handlers) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def protection_handler(event):
    if await check_privilege(event, "مميز"): return # المميز لا يطبق عليه الحظر
    
    gid = str(event.chat_id)
    # حماية الروابط والمعرفات
    if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+|@\S+)', event.raw_text):
        await event.delete()

# تشغيل البوت
print("--- سورس بوت تون يعمل الآن بنجاح ---")
client.run_until_disconnected()
