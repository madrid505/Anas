import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- إعدادات المراقبة ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الثوابت الأساسية ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "bot_data.db"
tagging_active = {}

# --- نظام قاعدة البيانات التراكمي ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        points INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'عضو'
    )""")
    conn.commit()
    conn.close()

def update_user_and_check_name(user):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM user_data WHERE user_id=?", (user.id,))
    row = cursor.fetchone()
    old_name = row[0] if row else user.full_name
    
    # التحديث التراكمي (النقاط +1 مع كل رسالة)
    cursor.execute("""
        INSERT INTO user_data (user_id, username, full_name, points) VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET 
            username=excluded.username, 
            full_name=excluded.full_name, 
            points=user_data.points + 1
    """, (user.id, user.username, user.full_name))
    conn.commit()
    conn.close()
    return old_name

# --- وظائف التحقق ---
async def is_admin(update: Update):
    u_id = update.effective_user.id
    if u_id == OWNER_ID: return True
    try:
        member = await update.effective_chat.get_member(u_id)
        return member.status in ['administrator', 'creator']
    except: return False

# --- معالجة الرسائل والذكاء الاصطناعي ---
async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # 1. كشف تغيير الاسم والنقاط
    old_name = update_user_and_check_name(user)
    if old_name != user.full_name:
        await update.message.reply_html(f"🔔 <b>تنبيه تغيير اسم!</b>\n👤 {user.mention_html()}\n⬅️ من: {old_name}\n➡️ إلى: {user.full_name}")

    # 2. الردود الملكية
    if text == "بوت":
        await update.message.reply_text("🌹 إدارة قروب مونوبولي ترحب بك 🌹\nنحن هنا لخدمتك، فلا تنسَ ذكر الله.")

    # 3. قائمة الأوامر الشاملة (امر)
    if text == "امر":
        if not await is_admin(update): return
        keyboard = [
            [InlineKeyboardButton("🔝 الرفع والتنزيل", callback_data="rank_menu"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
            [InlineKeyboardButton("🏆 ملك التفاعل", callback_data="king"), InlineKeyboardButton("📣 نداء (تاك)", callback_data="tag_menu")]
        ]
        await update.message.reply_text("✨ <b>قائمة مونوبولي Monopoly</b> ✨", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    # 4. نظام تاك الكل
    if text == "تاك الكل":
        if not await is_admin(update): return
        tagging_active[chat_id] = True
        await update.message.reply_text("📣 بدأ النداء الجماعي... لإيقافه أرسل: <b>ايقاف التاك</b>", parse_mode="HTML")
        
        conn = sqlite3.connect(DATABASE_FILE)
        members = conn.execute("SELECT user_id, full_name FROM user_data").fetchall()
        conn.close()

        for i in range(0, len(members), 5):
            if not tagging_active.get(chat_id): break
            chunk = members[i:i+5]
            mentions = " ".join([f"<a href='tg://user?id={m[0]}'>{m[1]}</a>" for m in chunk])
            try:
                await context.bot.send_message(chat_id=chat_id, text=mentions, parse_mode="HTML")
                await asyncio.sleep(2.5)
            except: continue

    if text == "ايقاف التاك":
        tagging_active[chat_id] = False
        await update.message.reply_text("🛑 تم إيقاف التاك.")

# --- الأزرار التفاعلية ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "king":
        conn = sqlite3.connect(DATABASE_FILE)
        king = conn.execute("SELECT full_name, points FROM user_data ORDER BY points DESC LIMIT 1").fetchone()
        conn.close()
        if king:
            await query.edit_message_text(f"🏆 <b>ملك التفاعل الحالي:</b>\n👤 الاسم: {king[0]}\n📈 النقاط التراكمية: {king[1]}", parse_mode="HTML")

    elif query.data == "detect":
        target = query.message.reply_to_message.from_user if query.message.reply_to_message else query.from_user
        conn = sqlite3.connect(DATABASE_FILE)
        res = conn.execute("SELECT points, rank FROM user_data WHERE user_id=?", (target.id,)).fetchone()
        conn.close()
        msg = f"🔍 <b>بيانات العضو:</b>\n🆔 الآيدي: <code>{target.id}</code>\n👤 الاسم: {target.full_name}\n🎖️ الرتبة: {res[1] if res else 'عضو'}\n📊 النقاط: {res[0] if res else 0}"
        await query.edit_message_text(msg, parse_mode="HTML")

# --- النشر التلقائي الآمن ---
async def auto_post(app):
    while True:
        await asyncio.sleep(900)
        for g_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(chat_id=g_id, text="📿 سبحان الله وبحمده، سبحان الله العظيم")
            except: continue

# --- نقطة الانطلاق الاستقراية ---
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(auto_post(app))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
