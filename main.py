# main.py

import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from config import TOKEN, OWNER_ID, ALLOWED_GROUPS, DATABASE_FILE, WELCOME_MESSAGE, POST_INTERVAL

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =========================
# قاعدة البيانات
# =========================
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    # جدول نقاط التفاعل
    c.execute('''CREATE TABLE IF NOT EXISTS points (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0
                 )''')
    # جدول الاسماء القديمة والجديدة
    c.execute('''CREATE TABLE IF NOT EXISTS names (
                    user_id INTEGER PRIMARY KEY,
                    old_name TEXT,
                    new_name TEXT
                 )''')
    conn.commit()
    conn.close()

# =========================
# أوامر الإدارة الأساسية
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text("البوت شغال ✅")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "جميع الأوامر متاحة عبر الأزرار أو الكتابة\nمثال: /points لمعرفة ملك التفاعل"
    await update.message.reply_text(text)

# =========================
# نظام ملك التفاعل
# =========================
async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, name, points FROM points ORDER BY points DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {row[1]} 👉👉\n🔥🔥 {row[2]} 🔥🔥\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("لا يوجد بيانات حتى الآن.")

# =========================
# الترحيب عند منادي البوت
# =========================
async def mention_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text(WELCOME_MESSAGE)

# =========================
# تسجيل الرسائل لملك التفاعل
# =========================
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.full_name
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT points FROM points WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE points SET points=points+1, name=? WHERE user_id=?", (name, user_id))
    else:
        c.execute("INSERT INTO points (user_id, name, points) VALUES (?, ?, ?)", (user_id, name, 1))
    conn.commit()
    conn.close()

# =========================
# نشر تلقائي للأذكار والادعية كل 15 دقيقة
# =========================
async def auto_post(application):
    while True:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        # هنا تضع جدول الادعية والاذكار
        c.execute("SELECT 'اذكار قصيرة'")  # مؤقتًا
        post = c.fetchone()[0]
        conn.close()
        for group_id in ALLOWED_GROUPS:
            try:
                await application.bot.send_message(chat_id=group_id, text=post)
            except Exception as e:
                logging.error(f"خطأ بالنشر التلقائي: {e}")
        await asyncio.sleep(POST_INTERVAL * 60)

# =========================
# نقطة البداية
# =========================
async def main():
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("points", points_command))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_messages))
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("mention"), mention_bot))

    # نشر تلقائي في الخلفية
    application.create_task(auto_post(application))

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
