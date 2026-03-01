import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الثابتة (تأكد من وجودها في متغيرات البيئة أو هنا) ---
TOKEN = "8509643139:AAG9r1U4FvxTV03RqiBXj9JxQEvGU2gHVN"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "bot_data.db"

# متغير للتحكم في "تاك الكل"
tagging_active = {}

# --- إدارة قاعدة البيانات (دمج Database.py داخلياً للأمان) ---
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

def update_user(user_id, username, full_name):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM user_data WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    old_name = row[0] if row else full_name
    cursor.execute("""
        INSERT INTO user_data (user_id, username, full_name) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name, points=points+1
    """, (user_id, username, full_name))
    conn.commit()
    conn.close()
    return old_name

# --- الوظائف الأساسية ---

async def is_admin(update: Update):
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True
    chat_member = await update.effective_chat.get_member(user_id)
    return chat_member.status in ['administrator', 'creator']

async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        return

    user = update.effective_user
    text = update.message.text.strip() if update.message.text else ""
    chat_id = update.effective_chat.id

    # 1. تحديث البيانات وكشف تغيير الاسم
    old_name = update_user(user.id, user.username, user.full_name)
    if old_name != user.full_name:
        await update.message.reply_html(f"⚠️ **تنبيه تغيير اسم!**\n\n👤 العضو: {user.mention_html()}\n⬅️ القديم: {old_name}\n➡️ الجديد: {user.full_name}")

    # 2. رد "بوت"
    if text == "بوت":
        await update.message.reply_text("🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\nنحن هنا لكي نجعلك سعيداً لا تجعل اللعبة تلهيك عن ذكر الله.")

    # 3. فتح قائمة "امر"
    if text == "امر":
        if not await is_admin(update): return
        keyboard = [
            [InlineKeyboardButton("🔝 الرفع والتنزيل", callback_data="rank_menu"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
            [InlineKeyboardButton("🚫 كتم / حظر", callback_data="admin_menu"), InlineKeyboardButton("📣 نداء (تاك)", callback_data="tag_menu")],
            [InlineKeyboardButton("🏆 ملك التفاعل", callback_data="king")],
        ]
        await update.message.reply_text("✨ **قائمة مونوبولي Monopoly** ✨\nإدارة المجموعات والحماية برؤية سحرية:", reply_markup=InlineKeyboardMarkup(keyboard))

    # 4. تفعيل "تاك الكل" بالنص
    if text == "تاك الكل":
        if not await is_admin(update): return
        tagging_active[chat_id] = True
        await update.message.reply_text("📣 بدأت عملية (تاك الكل)... أرسل 'ايقاف التاك' للإلغاء.")
        
        # جلب الأعضاء (هذه الطريقة تعمل للأعضاء النشطين في ذاكرة البوت)
        # ملاحظة: القيود البرمجية تمنع جلب كل الـ 100k عضو دفعة واحدة لكن سننادي المتفاعلين
        members = [] # في نسخة الإنتاج يتم جلبهم من قاعدة البيانات التي بنيناها
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name FROM user_data")
        members = cursor.fetchall()
        conn.close()

        for i in range(0, len(members), 5):
            if not tagging_active.get(chat_id): break
            chunk = members[i:i+5]
            mentions = " ".join([f"<a href='tg://user?id={m[0]}'>{m[1]}</a>" for m in chunk])
            await context.bot.send_message(chat_id=chat_id, text=mentions, parse_mode="HTML")
            await asyncio.sleep(2) # لتجنب الحظر من تلجرام

    # 5. إيقاف التاك
    if text == "ايقاف التاك":
        tagging_active[chat_id] = False
        await update.message.reply_text("🛑 تم إيقاف عملية التاك بنجاح.")

# --- معالج الأزرار التفاعلية ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "detect":
        user = query.message.reply_to_message.from_user if query.message.reply_to_message else query.from_user
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT points, rank FROM user_data WHERE user_id=?", (user.id,))
        res = cursor.fetchone()
        conn.close()
        
        msg = (f"🔍 **بيانات العضو الملكية:**\n\n"
               f"🆔 الآيدي: `{user.id}`\n"
               f"👤 الاسم: {user.full_name}\n"
               f"🌍 الدولة: {user.language_code if user.language_code else 'غير محددة'}\n"
               f"🎖️ الرتبة: {res[1] if res else 'عضو'}\n"
               f"📊 عدد الرسائل: {res[0] if res else 0}")
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif data == "king":
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, points FROM user_data ORDER BY points DESC LIMIT 1")
        king = cursor.fetchone()
        conn.close()
        if king:
            await query.edit_message_text(f"🏆 **ملك التفاعل حالياً:**\n\n👤 الاسم: {king[0]}\n📈 رصيد الرسائل: {king[1]}\n\nتفاعل أكثر لتصبح الملك القادم!")

# --- التشغيل الرئيسي ---
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ البوت يعمل الآن بكامل طاقته (مونوبولي)...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
