import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, OWNER_ID, ALLOWED_GROUPS, PROTECTED_USERS
from database import init_db, get_connection

init_db()

# --------------------- لوحة الأزرار ---------------------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king_points")],
        [InlineKeyboardButton("🛡️ إدارة الرتب", callback_data="manage_roles")],
        [InlineKeyboardButton("🔒 القفل/الفتح", callback_data="lock_unlock")],
        [InlineKeyboardButton("📝 الردود", callback_data="replies")],
        [InlineKeyboardButton("📣 نشر تلقائي", callback_data="auto_post")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --------------------- التعامل مع الضغط على الأزرار ---------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "king_points":
        await show_king_points(update)
    elif data == "manage_roles":
        await update.callback_query.edit_message_text("🛡️ أوامر إدارة الرتب")
    elif data == "lock_unlock":
        await update.callback_query.edit_message_text("🔒 القفل/الفتح")
    elif data == "replies":
        await update.callback_query.edit_message_text("📝 إدارة الردود")
    elif data == "auto_post":
        await update.callback_query.edit_message_text("📣 النشر التلقائي")
    else:
        await query.edit_message_text(f"تم اختيار: {data}")

# --------------------- ملك التفاعل ---------------------
async def show_king_points(update: Update):
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

# --------------------- أمر /start ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id not in ALLOWED_GROUPS:
        await update.message.reply_text("❌ هذه المجموعة غير مسموح بها للبوت")
        return
    await update.message.reply_text("مرحباً بك! اختر من القائمة:", reply_markup=main_menu_keyboard())

# --------------------- تتبع الرسائل ---------------------
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id not in ALLOWED_GROUPS:
        return
    user = update.message.from_user
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO points(user_id, name, points) VALUES(?,?,0)", (user.id, user.full_name))
    c.execute("UPDATE points SET points = points + 1, name=? WHERE user_id=?", (user.full_name, user.id))
    conn.commit()
    conn.close()

# --------------------- تتبع تغيير أسماء الأعضاء ---------------------
async def track_name_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    old_name = user.full_name
    new_name = user.full_name
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO name_changes(user_id, old_name, new_name) VALUES(?,?,?)", (user.id, old_name, new_name))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"📝 تغير الاسم: {old_name} ➡️ {new_name}\nID: {user.id}")

# --------------------- الردود التلقائية ---------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT response FROM replies WHERE trigger=?", (text,))
    row = c.fetchone()
    conn.close()
    if row:
        await update.message.reply_text(row[0])

# --------------------- إدارة الرتب ---------------------
async def manage_roles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ فقط المالك الأساسي يمكنه إدارة الرتب")
        return
    await update.message.reply_text("🛡️ أوامر الرتب: رفع/تنزيل/تعيين الرتب")

# --------------------- القفل والفتح ---------------------
async def lock_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔒 القفل/الفتح لكل أنواع المحتوى")

# --------------------- الحماية ---------------------
def is_protected(user_id):
    return user_id in PROTECTED_USERS

# --------------------- النشر التلقائي ---------------------
async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    for group_id in ALLOWED_GROUPS:
        await context.bot.send_message(chat_id=group_id, text="📿 دعاء أو ذكر تلقائي")

# --------------------- مهمة النشر كل 15 دقيقة ---------------------
async def scheduler(app):
    while True:
        await auto_post(app)
        await asyncio.sleep(900)  # 15 دقيقة

# --------------------- إعداد التطبيق ---------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_name_change))

# --------------------- تشغيل البوت ---------------------
if __name__ == "__main__":
    print("البوت شغال 🚀")
    asyncio.get_event_loop().create_task(scheduler(app))
    app.run_polling()
