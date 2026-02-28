import os
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- الإعدادات ---
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5010882230"))

ALLOWED_GROUPS = [
    int(os.getenv("GROUP_1", "-1002695848824")),
    int(os.getenv("GROUP_2", "-1003721123319")),
    int(os.getenv("GROUP_3", "-1002052564369"))
]

DATABASE_FILE = "bot_data.db"
POST_INTERVAL = 15  # دقائق

WELCOME_MESSAGE = (
    "🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\n"
    "نحن هنا لكي نجعلك سعيدا لا تجعل اللعبة ان تلهيك عن ذكر الله\n"
    "⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة\n"
    "⛔ يمنع منعا باتا التواصل مع المشرفات\n"
    "👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉"
)

PROTECTED_USERS = [OWNER_ID]

# --- قاعدة البيانات ---
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_points (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# --- وظائف البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text(WELCOME_MESSAGE)

# فتح القائمة عند كتابة كلمة "امر"
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_GROUPS:
        return

    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO user_points (user_id, points) VALUES (?,0)", (user_id,))
    cursor.execute("UPDATE user_points SET points = points + 1 WHERE user_id = ?", (user_id,))
    conn.commit()

    text = update.message.text.strip().lower()
    if text == "امر":
        keyboard = [
            [InlineKeyboardButton("رفع", callback_data="raise")],
            [InlineKeyboardButton("تنزيل", callback_data="lower")],
            [InlineKeyboardButton("اضف رد", callback_data="add_reply")],
            [InlineKeyboardButton("كتم", callback_data="mute")],
            [InlineKeyboardButton("طرد", callback_data="kick")],
            [InlineKeyboardButton("تقييد", callback_data="restrict")],
            [InlineKeyboardButton("حظر", callback_data="ban")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# --- التعامل مع أزرار القائمة ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    # حماية المالك
    if user_id in PROTECTED_USERS and action in ["kick", "ban", "mute", "restrict"]:
        await query.edit_message_text("⚠️ لا يمكنك تطبيق هذا الإجراء على المالك.")
        return

    # وظائف الأزرار (يمكن تعديل التفاصيل حسب الحاجة)
    if action == "raise":
        await query.edit_message_text("✅ تم رفع العضو.")
    elif action == "lower":
        await query.edit_message_text("✅ تم تنزيل العضو.")
    elif action == "add_reply":
        await query.edit_message_text("✅ يمكنك الآن إضافة ردود تلقائية.")
    elif action == "mute":
        await query.edit_message_text("✅ تم كتم العضو.")
    elif action == "kick":
        await query.edit_message_text("✅ تم طرد العضو.")
    elif action == "restrict":
        await query.edit_message_text("✅ تم تقييد العضو.")
    elif action == "ban":
        await query.edit_message_text("✅ تم حظر العضو.")
    else:
        await query.edit_message_text(f"⚠️ لم يتم التعرف على الإجراء: {action}")

# --- النشر التلقائي ---
async def auto_post(app):
    while True:
        for group_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(chat_id=group_id, text="📿 دعاء أو ذكر تلقائي")
            except Exception as e:
                print(f"Error sending to {group_id}: {e}")
        await asyncio.sleep(POST_INTERVAL * 60)

# --- المهام الخلفية ---
async def scheduler(app):
    asyncio.create_task(auto_post(app))

# --- تشغيل البوت ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(scheduler(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
