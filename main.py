import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TOKEN, OWNER_ID, ALLOWED_GROUPS, WELCOME_MESSAGE, PROTECTED_USERS, POST_INTERVAL
import database as db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# ==========================
# الوظائف الأساسية
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text(WELCOME_MESSAGE)

async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    db.add_user(user.id, user.username or user.first_name)
    db.update_message_count(user.id)

async def top_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = db.get_top_user()
    if top:
        msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {top[0]} 👉👉\n🔥🔥 {top[1]} 🔥🔥\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
        await update.message.reply_text(msg)

# ==========================
# الردود المخصصة
# ==========================
async def custom_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    reply = db.get_custom_reply(text)
    if reply:
        await update.message.reply_text(reply)

# ==========================
# زرائر تفاعلية
# ==========================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "top_user":
        top = db.get_top_user()
        if top:
            msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {top[0]} 👉👉\n🔥🔥 {top[1]} 🔥🔥\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
            await query.edit_message_text(msg)

def main_buttons():
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="top_user")],
        # يمكن إضافة أزرار أخرى هنا
    ]
    return InlineKeyboardMarkup(keyboard)

# ==========================
# تتبع تغيير الاسم
# ==========================
async def track_username_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.update_username(user.id, user.username or user.first_name)
    await update.message.reply_text(
        f"تم تغيير الاسم:\nالاسم القديم: {user.first_name}\nالاسم الجديد: {user.username}"
    )

# ==========================
# النشر التلقائي
# ==========================
async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    for group_id in ALLOWED_GROUPS:
        await context.bot.send_message(chat_id=group_id, text="✨ تذكير تلقائي ✨\nذكر الله وحفظ الوقت!")
        
# ==========================
# إعداد التطبيق والبوت
# ==========================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ملك_التفاعل", top_user))

    # رسائل عامة
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_messages))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), custom_reply))

    # أزرار
    app.add_handler(CallbackQueryHandler(button_callback))

    # تتبع تغيير الاسم
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_username_change))
    
    # جدولة النشر التلقائي كل POST_INTERVAL دقيقة
    job_queue = app.job_queue
    job_queue.run_repeating(auto_post, interval=POST_INTERVAL*60, first=10)

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
