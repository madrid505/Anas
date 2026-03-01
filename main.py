import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# إعداد السجلات (Logging) لمراقبة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الثابتة ---
# محاولة جلب التوكن من البيئة، وإذا لم يوجد نستخدم التوكن الذي زودتني به
TOKEN = os.getenv("TOKEN", "8509643139:AAG9r1U4FvxTV03RqiBXj9JxQEvGU2gHVN")
OWNER_ID = int(os.getenv("OWNER_ID", "5010882230"))

# معرفات المجموعات المسموح لها بالعمل
ALLOWED_GROUPS = [
    int(os.getenv("GROUP_1", "-1002695848824")),
    int(os.getenv("GROUP_2", "-1003721123319")),
    int(os.getenv("GROUP_3", "-1002052564369"))
]

DATABASE_FILE = "bot_data.db"
POST_INTERVAL = 15  # بالدقائق

WELCOME_MESSAGE = (
    "🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\n"
    "نحن هنا لكي نجعلك سعيدا لا تجعل اللعبة ان تلهيك عن ذكر الله\n"
    "⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة\n"
    "⛔ يمنع منعا باتا التواصل مع المشرفات\n"
    "👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉"
)

PROTECTED_USERS = [OWNER_ID]

# --- إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_points (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    return conn

# --- وظائف المساعدة ---
async def is_admin(update: Update):
    """التحقق مما إذا كان المستخدم مشرفاً أو المالك"""
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
    chat_member = await update.effective_chat.get_member(user_id)
    return chat_member.status in ['administrator', 'creator']

# --- وظائف البوت الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_GROUPS:
        return
    await update.message.reply_text(WELCOME_MESSAGE)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_GROUPS:
        return

    user_id = update.effective_user.id
    
    # تحديث النقاط
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_points (user_id, points) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE user_points SET points = points + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    text = update.message.text.strip().lower()
    if text == "امر":
        # لا يظهر قائمة الأوامر إلا للمشرفين أو المالك
        if not await is_admin(update):
            return

        keyboard = [
            [InlineKeyboardButton("إحصائيات النقاط 📊", callback_data="points")],
            [InlineKeyboardButton("كتم 🤐", callback_data="mute"), InlineKeyboardButton("طرد 🚷", callback_data="kick")],
            [InlineKeyboardButton("حظر 🚫", callback_data="ban"), InlineKeyboardButton("تقييد ⚠️", callback_data="restrict")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🛠 **قائمة التحكم بالحماية:**\nقم بالرد على رسالة المستخدم ثم اختر الإجراء:", reply_markup=reply_markup)

# --- التعامل مع أزرار التحكم ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    # التحقق من الصلاحية (فقط المالك والمشرفين)
    if not await is_admin(update):
        await query.answer("❌ ليس لديك صلاحية التحكم.", show_alert=True)
        return

    action = query.data
    
    # التأكد من وجود رسالة يتم الرد عليها لتنفيذ الإجراء
    if not query.message.reply_to_message and action != "points":
        await query.edit_message_text("⚠️ يجب أن تستخدم الأمر بالرد على رسالة العضو المستهدف.")
        return

    target_user = query.message.reply_to_message.from_user if query.message.reply_to_message else None
    
    if target_user and target_user.id in PROTECTED_USERS:
        await query.answer("🛡️ لا يمكن المساس بالمالك!", show_alert=True)
        return

    try:
        if action == "kick":
            await context.bot.ban_chat_member(chat_id, target_user.id)
            await context.bot.unban_chat_member(chat_id, target_user.id) # لإتاحة العودة لاحقاً (طرد فقط)
            await query.edit_message_text(f"✅ تم طرد العضو {target_user.first_name}")
            
        elif action == "ban":
            await context.bot.ban_chat_member(chat_id, target_user.id)
            await query.edit_message_text(f"🚫 تم حظر العضو {target_user.first_name} نهائياً.")

        elif action == "mute":
            permissions = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(chat_id, target_user.id, permissions=permissions)
            await query.edit_message_text(f"🤐 تم كتم العضو {target_user.first_name}")

        elif action == "points":
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
            res = cursor.fetchone()
            pts = res[0] if res else 0
            await query.answer(f"رصيد نقاطك هو: {pts}", show_alert=True)
            conn.close()

    except Exception as e:
        await query.edit_message_text(f"❌ فشل الإجراء: {str(e)}")

# --- النشر التلقائي والأذكار ---
async def auto_post_task(app):
    while True:
        await asyncio.sleep(POST_INTERVAL * 60)
        for group_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(
                    chat_id=group_id, 
                    text="✨ **تذكير** ✨\nلا تنسَ ذكر الله.. سبحان الله وبحمده، سبحان الله العظيم."
                )
            except Exception as e:
                logging.error(f"Error in auto_post to {group_id}: {e}")

# --- التشغيل الرئيسي ---
async def main():
    init_db() # تهيئة القاعدة عند البدء
    
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    # تشغيل مهمة النشر التلقائي في الخلفية
    asyncio.create_task(auto_post_task(app))

    print("✅ البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
