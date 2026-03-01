import os
import asyncio
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- إعدادات السجلات (Logging) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- الثوابت والإعدادات ---
TOKEN = "8509643139:AAG9r1U4FvxTV03RqiBXj9JxQEvGU2gHVN"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "bot_data.db"
tagging_active = {}

# --- إدارة قاعدة البيانات الشاملة ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # جدول البيانات الأساسية (نقاط، رتب، أسماء)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        points INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'عضو'
    )""")
    # جدول الردود المخصصة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_replies (
        keyword TEXT PRIMARY KEY,
        reply TEXT
    )""")
    conn.commit()
    conn.close()

def update_user_full(user_id, username, full_name):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM user_data WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    old_name = row[0] if row else full_name
    
    # التحديث التراكمي للنقاط وتحديث البيانات
    cursor.execute("""
        INSERT INTO user_data (user_id, username, full_name, points) 
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET 
            username=excluded.username, 
            full_name=excluded.full_name, 
            points=user_data.points + 1
    """, (user_id, username, full_name))
    conn.commit()
    conn.close()
    return old_name

def set_user_rank(user_id, new_rank):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_data SET rank=? WHERE user_id=?", (new_rank, user_id))
    conn.commit()
    conn.close()

# --- وظائف الحماية والتحقق ---
async def check_admin(update: Update):
    u_id = update.effective_user.id
    if u_id == OWNER_ID: return True
    try:
        member = await update.effective_chat.get_member(u_id)
        return member.status in ['administrator', 'creator']
    except: return False

# --- معالجة الرسائل الرئيسية ---
async def global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # 1. تحديث النقاط وكشف تغيير الاسم
    old_name = update_user_full(user.id, user.username, user.full_name)
    if old_name != user.full_name:
        alert = (f"🔔 <b>تنبيه تغيير اسم!</b>\n\n"
                 f"👤 العضو: {user.mention_html()}\n"
                 f"⬅️ الاسم القديم: {old_name}\n"
                 f"➡️ الاسم الجديد: {user.full_name}")
        await update.message.reply_html(alert)

    # 2. الاستجابة لكلمة "بوت"
    if text == "بوت":
        welcome = (f"🌹 <b>إدارة قروب مونوبولي ترحب بك</b> 🌹\n\n"
                   f"أهلاً بك {user.first_name} في مجموعتنا.\n"
                   f"⛔ يمنع اللعب أثناء رفع الأذان.\n"
                   f"⛔ يمنع التواصل مع المشرفات.\n"
                   f"👈 للاستفسار تواصل مع Anas أو Sakher.")
        await update.message.reply_html(welcome)

    # 3. فتح قائمة "امر" (مونوبولي)
    if text == "امر":
        if not await check_admin(update): return
        keyboard = [
            [InlineKeyboardButton("🔝 الرفع والتنزيل", callback_data="rank_menu"), 
             InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
            [InlineKeyboardButton("🚫 كتم / حظر", callback_data="admin_actions"), 
             InlineKeyboardButton("📣 نداء (تاك)", callback_data="tag_menu")],
            [InlineKeyboardButton("🏆 ملك التفاعل", callback_data="show_king"), 
             InlineKeyboardButton("📝 الردود", callback_data="reply_mgmt")],
        ]
        await update.message.reply_text(
            "✨ <b>قائمة مونوبولي Monopoly</b> ✨\nلوحة التحكم الشاملة بالإدارة والحماية:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # 4. نظام "تاك الكل" و "ايقاف التاك"
    if text == "تاك الكل":
        if not await check_admin(update): return
        tagging_active[chat_id] = True
        await update.message.reply_text("📣 بدأت عملية (تاك الكل) لجميع الأعضاء المتفاعلين...\nلإيقافها أرسل: <b>ايقاف التاك</b>", parse_mode="HTML")
        
        conn = sqlite3.connect(DATABASE_FILE)
        members = conn.execute("SELECT user_id, full_name FROM user_data").fetchall()
        conn.close()

        for i in range(0, len(members), 5):
            if not tagging_active.get(chat_id): break
            chunk = members[i:i+5]
            mention_line = " ".join([f"<a href='tg://user?id={m[0]}'>{m[1]}</a>" for m in chunk])
            try:
                await context.bot.send_message(chat_id=chat_id, text=mention_line, parse_mode="HTML")
                await asyncio.sleep(2.5) # فاصل زمني للأمان
            except: continue

    if text == "ايقاف التاك":
        if not await check_admin(update): return
        tagging_active[chat_id] = False
        await update.message.reply_text("🛑 تم إيقاف عملية التاك بنجاح.")

    # 5. أوامر الرفع والتنزيل النصية
    if text == "رفع مميز" and update.message.reply_to_message:
        if not await check_admin(update): return
        target = update.message.reply_to_message.from_user
        set_user_rank(target.id, "عضو مميز ✨")
        await update.message.reply_text(f"✅ تم رفع {target.first_name} إلى رتبة مميز.")

    if text == "تنزيل" and update.message.reply_to_message:
        if not await check_admin(update): return
        target = update.message.reply_to_message.from_user
        set_user_rank(target.id, "عضو")
        await update.message.reply_text(f"✅ تم تنزيل {target.first_name} إلى رتبة عضو.")

# --- معالج الأزرار التفاعلية ---
async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "detect":
        target = query.message.reply_to_message.from_user if query.message.reply_to_message else query.from_user
        conn = sqlite3.connect(DATABASE_FILE)
        res = conn.execute("SELECT points, rank FROM user_data WHERE user_id=?", (target.id,)).fetchone()
        conn.close()
        
        points = res[0] if res else 0
        rank = res[1] if res else "عضو"
        msg = (f"🔍 <b>كشف بيانات العضو:</b>\n\n"
               f"👤 الاسم: {target.full_name}\n"
               f"🆔 الآيدي: <code>{target.id}</code>\n"
               f"🎖️ الرتبة: {rank}\n"
               f"🌍 الدولة: {target.language_code if target.language_code else 'غير محددة'}\n"
               f"📊 النقاط التراكمية: {points}\n"
               f"📈 مستوى التفاعل: {'مرتفع' if points > 100 else 'متوسط'}")
        await query.edit_message_text(msg, parse_mode="HTML")

    elif data == "show_king":
        conn = sqlite3.connect(DATABASE_FILE)
        king = conn.execute("SELECT full_name, points FROM user_data ORDER BY points DESC LIMIT 1").fetchone()
        conn.close()
        if king:
            await query.edit_message_text(
                f"🏆 <b>ملك التفاعل الحالي:</b>\n\n👤 الاسم: {king[0]}\n📈 مجموع الرسائل: {king[1]}\n\nتفاعل أكثر لتنتزع اللقب!",
                parse_mode="HTML"
            )

# --- المهام المجدولة (النشر التلقائي) ---
async def auto_post_task(app):
    while True:
        await asyncio.sleep(900) # كل 15 دقيقة
        for g_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(chat_id=g_id, text="📿 ذكر الله راحة للقلوب.. سبحان الله وبحمده.")
            except: continue

# --- تشغيل البوت ---
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_handler))
    app.add_handler(CallbackQueryHandler(on_button_click))
    
    asyncio.create_task(auto_post_task(app))
    
    print("🚀 تم تشغيل بوت مونوبولي بنسخته الكاملة...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
