import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = "8509643139:AAG9r1U4FvxTV03RqiBXj9JxQEvGU2gHVN"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "bot_data.db"
tagging_active = {}

# --- إدارة قاعدة البيانات (نقاط تراكمية ورتب) ---
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

def update_user_and_get_old_name(user_id, username, full_name):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM user_data WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    old_name = row[0] if row else full_name
    
    # تحديث تراكمي للنقاط والبيانات
    cursor.execute("""
        INSERT INTO user_data (user_id, username, full_name, points) VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET 
            username=excluded.username, 
            full_name=excluded.full_name, 
            points=points+1
    """, (user_id, username, full_name))
    conn.commit()
    conn.close()
    return old_name

# --- المعالجات الأساسية ---

async def is_admin(update: Update):
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True
    try:
        chat_member = await update.effective_chat.get_member(user_id)
        return chat_member.status in ['administrator', 'creator']
    except: return False

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        return

    user = update.effective_user
    text = update.message.text.strip() if update.message.text else ""
    chat_id = update.effective_chat.id

    # 1. مراقب الأسماء + زيادة النقاط التراكمية
    old_name = update_user_and_get_old_name(user.id, user.username, user.full_name)
    if old_name != user.full_name:
        await update.message.reply_html(f"🔔 **تغيير اسم مكتشف!**\n👤 {user.mention_html()}\n⬅️ من: {old_name}\n➡️ إلى: {user.full_name}")

    # 2. رد "بوت"
    if text == "بوت":
        await update.message.reply_text("🌹 ادارة قروب مونوبولي ترحب بك 🌹\nنحن هنا لنسعدك، فلا تلهك اللعبة عن ذكر الله.")

    # 3. قائمة الأوامر (مونوبولي Monopoly)
    if text == "امر":
        if not await is_admin(update): return
        keyboard = [
            [InlineKeyboardButton("🔝 الرفع والتنزيل", callback_data="rank_menu"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
            [InlineKeyboardButton("🏆 ملك التفاعل", callback_data="king"), InlineKeyboardButton("📣 نداء (تاك)", callback_data="tag_menu")]
        ]
        await update.message.reply_text("✨ **قائمة مونوبولي Monopoly** ✨", reply_markup=InlineKeyboardMarkup(keyboard))

    # 4. نظام تاك الكل
    if text == "تاك الكل":
        if not await is_admin(update): return
        tagging_active[chat_id] = True
        await update.message.reply_text("📣 بدأ (تاك الكل)... لإيقافه أرسل: ايقاف التاك")
        
        conn = sqlite3.connect(DATABASE_FILE)
        members = conn.execute("SELECT user_id, full_name FROM user_data").fetchall()
        conn.close()

        for i in range(0, len(members), 5):
            if not tagging_active.get(chat_id): break
            chunk = members[i:i+5]
            mentions = " ".join([f"<a href='tg://user?id={m[0]}'>{m[1]}</a>" for m in chunk])
            await context.bot.send_message(chat_id=chat_id, text=mentions, parse_mode="HTML")
            await asyncio.sleep(2.5)

    if text == "ايقاف التاك":
        tagging_active[chat_id] = False
        await update.message.reply_text("🛑 تم إيقاف التاك.")

# --- الأزرار التفاعلية ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "king":
        conn = sqlite3.connect(DATABASE_FILE)
        king = conn.execute("SELECT full_name, points FROM user_data ORDER BY points DESC LIMIT 1").fetchone()
        conn.close()
        if king:
            await query.edit_message_text(f"🏆 **ملك التفاعل (تراكمي):**\n👤 الاسم: {king[0]}\n📈 مجموع الرسائل: {king[1]}")

    elif data == "detect":
        target = query.message.reply_to_message.from_user if query.message.reply_to_message else query.from_user
        conn = sqlite3.connect(DATABASE_FILE)
        res = conn.execute("SELECT points, rank FROM user_data WHERE user_id=?", (target.id,)).fetchone()
        conn.close()
        msg = f"🔍 **بيانات:**\n🆔 الآيدي: `{target.id}`\n👤 الاسم: {target.full_name}\n🎖️ الرتبة: {res[1] if res else 'عضو'}\n📊 النقاط: {res[0] if res else 0}"
        await query.edit_message_text(msg, parse_mode="Markdown")

# --- النشر التلقائي (مع إصلاح خطأ Chat not found) ---
async def auto_post(app):
    while True:
        await asyncio.sleep(900) # 15 دقيقة
        for group_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(chat_id=group_id, text="📿 سبحان الله وبحمده، سبحان الله العظيم")
            except Exception as e:
                logging.error(f"فشل النشر في {group_id}: {e}") # سيستمر البوت ولن يتوقف

# --- التشغيل ---
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # تشغيل النشر التلقائي كمهمة خلفية آمنة
    asyncio.create_task(auto_post(app))
    
    print("✅ البوت يعمل الآن - نسخة مونوبولي الكاملة")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
