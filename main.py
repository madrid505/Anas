# main.py

import logging
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
)
from config import TOKEN, OWNER_ID, ALLOWED_GROUPS, WELCOME_MESSAGE, POST_INTERVAL, PROTECTED_USERS
import database as db

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- وظائف مساعدة ---

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text(WELCOME_MESSAGE)

# --- قائمة الأزرار ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king")],
        [InlineKeyboardButton("📊 كشف", callback_data="check")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "king":
        points = db.get_points(query.from_user.id)
        await query.edit_message_text(f"👑👑 ملك التفاعل 👑👑\n\n"
                                      f"👈👈 {query.from_user.username} 👉👉\n"
                                      f"🔥🔥 {points} 🔥🔥\n"
                                      f"⭐⭐ استمر بالمشاركة يا بطل ⭐⭐")
    elif query.data == "check":
        info = db.get_user_info(query.from_user.id)
        if info:
            await query.edit_message_text(f"الاسم: {info['username']}\n"
                                          f"عدد الرسائل: {info['messages']}\n"
                                          f"الدولة: {info['country']}")
        else:
            await query.edit_message_text("لا يوجد بيانات لهذا العضو.")

# --- تتبع الرسائل لملك التفاعل ---
async def track_messages(update: Update, context: CallbackContext):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    user = update.effective_user
    db.add_user(user.id, user.username)
    db.increment_points(user.id)
    db.increment_messages(user.id)

# --- كشف ---
async def check_command(update: Update, context: CallbackContext):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    reply = update.message.reply_to_message
    if reply:
        user = reply.from_user
        info = db.get_user_info(user.id)
        if info:
            await update.message.reply_text(f"الاسم: {info['username']}\n"
                                            f"ID: {user.id}\n"
                                            f"عدد الرسائل: {info['messages']}\n"
                                            f"الدولة: {info['country']}")
        else:
            await update.message.reply_text("لا توجد بيانات لهذا العضو.")

# --- تتبع تغيير الاسم ---
async def username_tracker(update: Update, context: CallbackContext):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    user = update.effective_user
    db.add_user(user.id, user.username)

# --- النشر التلقائي ---
async def auto_posting(context: CallbackContext):
    for group_id in ALLOWED_GROUPS:
        await context.bot.send_message(chat_id=group_id, text="🔔 النشر التلقائي: تذكير ومحتوى مفيد 🔔")

# --- إضافة معالج للنشر التلقائي كل POST_INTERVAL دقيقة ---
async def schedule_auto_posting(app):
    while True:
        await auto_posting(app)
        await asyncio.sleep(POST_INTERVAL * 60)

# --- نقطة الدخول الرئيسية ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر وقائمة الأزرار
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("كشف", check_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.USERNAME, username_tracker))
    app.add_handler(CallbackQueryHandler(menu_handler))

    # بدء النشر التلقائي في الخلفية
    app.job_queue.run_repeating(auto_posting, interval=POST_INTERVAL*60, first=10)

    # تشغيل البوت
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
