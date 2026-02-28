import logging
import os
import sqlite3
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from config import (
    TOKEN,
    OWNER_ID,
    ALLOWED_GROUPS,
    DATABASE_FILE,
    POST_INTERVAL,
    WELCOME_MESSAGE,
    PROTECTED_USERS
)

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========================
# قاعدة البيانات
# ========================
conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS custom_replies (
    keyword TEXT PRIMARY KEY,
    reply TEXT
)
""")
conn.commit()

# ========================
# وظائف مساعدة
# ========================
async def check_allowed_group(update: Update):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return False
    return True

async def add_point(user_id: int, username: str):
    cursor.execute("INSERT OR IGNORE INTO user_stats (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("UPDATE user_stats SET points = points + 1, username=? WHERE user_id = ?", (username, user_id))
    conn.commit()

async def get_king_of_activity():
    cursor.execute("SELECT username, points FROM user_stats ORDER BY points DESC LIMIT 1")
    return cursor.fetchone()

async def send_welcome(update: Update):
    await update.message.reply_text(WELCOME_MESSAGE)

# ========================
# أوامر الطرد والكتم والحظر
# ========================
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    # تحقق من الصلاحيات
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if target and target.id not in PROTECTED_USERS:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"تم حظر {target.full_name}")
    else:
        await update.message.reply_text("لا يمكن حظر هذا المستخدم")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    target_id = context.args[0] if context.args else None
    if target_id:
        await context.bot.unban_chat_member(update.effective_chat.id, int(target_id))
        await update.message.reply_text(f"تم رفع الحظر عن المستخدم {target_id}")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if target and target.id not in PROTECTED_USERS:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=None)
        await update.message.reply_text(f"تم كتم {target.full_name}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if target:
        # إعادة الصلاحيات العادية
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=None)
        await update.message.reply_text(f"تم رفع الكتم عن {target.full_name}")

# ========================
# الردود المخصصة
# ========================
async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    try:
        keyword = context.args[0]
        reply_text = " ".join(context.args[1:])
        cursor.execute("INSERT OR REPLACE INTO custom_replies (keyword, reply) VALUES (?, ?)", (keyword, reply_text))
        conn.commit()
        await update.message.reply_text(f"تم إضافة الرد على '{keyword}'")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

async def remove_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_allowed_group(update): return
    keyword = context.args[0] if context.args else None
    if keyword:
        cursor.execute("DELETE FROM custom_replies WHERE keyword=?", (keyword,))
        conn.commit()
        await update.message.reply_text(f"تم حذف الرد '{keyword}'")

async def check_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text
    cursor.execute("SELECT reply FROM custom_replies WHERE keyword=?", (msg_text,))
    row = cursor.fetchone()
    if row:
        await update.message.reply_text(row[0])

# ========================
# ملك التفاعل (نقاط المشاركات)
# ========================
async def track_message(update: Update):
    if not await check_allowed_group(update): return
    user = update.message.from_user
    await add_point(user.id, user.full_name)

async def announce_king(context: ContextTypes.DEFAULT_TYPE):
    king = await get_king_of_activity()
    if king:
        username, points = king
        msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {username} 👉👉\n🔥🔥 {points} 🔥🔥\n\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
        for group in ALLOWED_GROUPS:
            await context.bot.send_message(chat_id=group, text=msg)

# ========================
# التحقق من تغيير الاسم
# ========================
async def monitor_username_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            # يمكنك إضافة قاعدة بيانات للاحتفاظ بالاسم القديم
            pass

# ========================
# النشر التلقائي
# ========================
async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    messages = [
        "✨ دعاء اليوم ✨",
        "📿 تسبيح ✨",
        "📖 حديث شريف ✨",
        "💡 حكمة وموعظة ✨"
    ]
    msg = messages[datetime.utcnow().minute % len(messages)]
    for group in ALLOWED_GROUPS:
        await context.bot.send_message(chat_id=group, text=msg)

# ========================
# بدء التطبيق
# ========================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_reply))

    # أوامر الإدارة
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("add_reply", add_reply))
    app.add_handler(CommandHandler("remove_reply", remove_reply))

    # النشر التلقائي كل POST_INTERVAL دقيقة
    app.job_queue.run_repeating(auto_post, interval=POST_INTERVAL*60, first=10)
    # ملك التفاعل كل أسبوع
    app.job_queue.run_repeating(announce_king, interval=7*24*60*60, first=15)

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
