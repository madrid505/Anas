import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)
from config import TOKEN, OWNER_ID, ALLOWED_GROUPS
from database import init_db, get_connection

# تهيئة قاعدة البيانات
init_db()

# قائمة الأوامر الأساسية بالزر
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king_points")],
        [InlineKeyboardButton("🛡️ رفع/تنزيل رتب", callback_data="manage_roles")],
        [InlineKeyboardButton("🔒 القفل/الفتح", callback_data="lock_unlock")],
        [InlineKeyboardButton("📝 الردود", callback_data="replies")],
        [InlineKeyboardButton("📣 نشر تلقائي", callback_data="auto_post")],
    ]
    return InlineKeyboardMarkup(keyboard)

# الرد على زر القائمة
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "king_points":
        await show_king_points(update, context)
    elif data == "manage_roles":
        await query.edit_message_text("أوامر رفع/تنزيل الرتب هنا...")
    elif data == "lock_unlock":
        await query.edit_message_text("أوامر القفل والفتح هنا...")
    elif data == "replies":
        await query.edit_message_text("إدارة الردود هنا...")
    elif data == "auto_post":
        await query.edit_message_text("تم تفعيل النشر التلقائي كل 15 دقيقة")

# عرض ملك التفاعل
async def show_king_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, points FROM points ORDER BY points DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        name, points = row
        text = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {name} 👉👉\n🔥🔥 {points} 🔥🔥\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
    else:
        text = "لا يوجد بيانات حتى الآن"
    await update.callback_query.edit_message_text(text=text)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك! اختر من القائمة:", 
        reply_markup=main_menu_keyboard()
    )

# تتبع الرسائل لإحتساب النقاط
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO points(user_id, name, points) VALUES(?,?,0)", (user.id, user.full_name))
    c.execute("UPDATE points SET points = points + 1, name=? WHERE user_id=?", (user.full_name, user.id))
    conn.commit()
    conn.close()

# إعداد التطبيق
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))

# تشغيل البوت
if __name__ == "__main__":
    print("البوت شغال 🚀")
    app.run_polling()
