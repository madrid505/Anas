import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# إعداد السجلات بشكل احترافي
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8509643139:AAG9r1U4FvxTV03RqiBXj9JxQEvGU2gHVN"
OWNER_ID = 5010882230
# تأكد من أن هذه الأرقام صحيحة 100% في مجموعاتك
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "bot_data.db"

# --- الحماية من الانهيار وقاعدة البيانات ---
def init_db():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.execute("""CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, points INTEGER DEFAULT 0, rank TEXT DEFAULT 'عضو'
        )""")
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error Database: {e}")

def update_user_data(user):
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM user_data WHERE user_id=?", (user.id,))
        row = cursor.fetchone()
        old_name = row[0] if row else user.full_name
        
        cursor.execute("""
            INSERT INTO user_data (user_id, username, full_name, points) VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET full_name=excluded.full_name, points=points+1
        """, (user.id, user.username, user.full_name))
        conn.commit()
        conn.close()
        return old_name
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        return user.full_name

# --- المعالج الرئيسي ---
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # 1. كشف تغيير الاسم + زيادة النقاط (تراكمي)
    old_name = update_user_data(user)
    if old_name != user.full_name:
        await update.message.reply_html(f"⚠️ <b>تنبيه تغيير اسم!</b>\n👤 {user.mention_html()}\n⬅️ من: {old_name}\n➡️ إلى: {user.full_name}")

    # 2. رد "بوت"
    if text == "بوت":
        await update.message.reply_text("🌹 إدارة قروب مونوبولي ترحب بك 🌹\nنحن هنا لخدمتك، اذكر الله دائماً.")

    # 3. القائمة السحرية
    if text == "امر":
        keyboard = [
            [InlineKeyboardButton("🔝 الرفع والتنزيل", callback_data="none"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
            [InlineKeyboardButton("🏆 ملك التفاعل", callback_data="king"), InlineKeyboardButton("📣 نداء (تاك)", callback_data="tag_menu")]
        ]
        await update.message.reply_text("✨ <b>قائمة مونوبولي Monopoly</b> ✨", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# --- النشر التلقائي المحمي ---
async def auto_post(app):
    while True:
        await asyncio.sleep(900) # كل 15 دقيقة
        for group_id in ALLOWED_GROUPS:
            try:
                # محاولة إرسال الرسالة، وإذا فشل لا ينهار البوت
                await app.bot.send_message(chat_id=group_id, text="📿 سبحان الله وبحمده، سبحان الله العظيم")
            except Exception:
                continue # تخطي المجموعة التي تسبب خطأ

# --- تشغيل البوت ---
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    
    # تشغيل المهام الخلفية
    asyncio.create_task(auto_post(app))
    
    print("✅ البوت يعمل الآن - نسخة الحماية الكاملة")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
