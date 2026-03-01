import asyncio
import sqlite3
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler, CommandHandler

# --- الإعدادات الأساسية ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "monopoly_pro.db"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- محرك قاعدة البيانات ---
async def init_db():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, 
            points INTEGER DEFAULT 0, rank TEXT DEFAULT 'عضو', msgs_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY, locked_media TEXT DEFAULT '', welcome_enabled INTEGER DEFAULT 1)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS replies (keyword TEXT PRIMARY KEY, response TEXT)""")
        await db.commit()

# --- دالة التحقق من الرتبة ---
async def get_user_rank(user_id):
    if user_id == OWNER_ID: return "المالك الأساسي 👑"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT rank FROM users WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "عضو"

# --- معالج الرسائل الرئيسي ---
async def monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS: return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # 1. تحديث البيانات والعد التراكمي
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""INSERT INTO users (user_id, username, full_name, points, msgs_count) 
            VALUES (?, ?, ?, 1, 1) ON CONFLICT(user_id) 
            DO UPDATE SET points=points+1, msgs_count=msgs_count+1, full_name=excluded.full_name""",
            (user.id, user.username, user.full_name))
        await db.commit()

    # 2. كشف تغيير الاسم
    if context.user_data.get('old_name') and context.user_data['old_name'] != user.full_name:
        await update.message.reply_text(f"⚠️ تغيير اسم!\nID: {user.id}\nالقديم: {context.user_data['old_name']}\nالجديد: {user.full_name}")
    context.user_data['old_name'] = user.full_name

    # 3. الرد على "بوت"
    if text == "بوت" or text == "يا بوت":
        resp = ("🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\nنحن هنا لكي نجعلك سعيدا لا تجعل اللعبة ان تلهيك عن ذكر الله\n"
                "⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة ⛔\n⛔يمنع منعا باتا التواصل مع المشرفات⛔\n"
                "👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉")
        await update.message.reply_text(resp)

    # 4. معالجة الأوامر النصية (رفع/تنزيل/حظر)
    await handle_text_commands(update, context, text)

# --- معالجة الأوامر النصية ---
async def handle_text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    user_rank = await get_user_rank(update.effective_user.id)
    is_admin = user_rank in ["المالك الأساسي 👑", "مدير", "أدمن"]
    
    # أوامر الكشف
    if text == "كشف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT points, rank FROM users WHERE user_id=?", (target.id,)) as cursor:
                row = await cursor.fetchone()
                p, r = (row[0], row[1]) if row else (0, "عضو")
        await update.message.reply_text(f"🔍 كشف البيانات:\nالاسم: {target.full_name}\nID: {target.id}\nالرسائل: {p}\nالرتبة: {r}")

    # أوامر الرفع (مثال)
    if text == "رفع مدير" and is_admin and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if target.id == OWNER_ID: return
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute("UPDATE users SET rank='مدير' WHERE user_id=?", (target.id,))
            await db.commit()
        await update.message.reply_text(f"✅ تم رفع {target.first_name} لمرتبة مدير")

    # قائمة الأوامر (امر)
    if text == "امر":
        await show_main_menu(update)

# --- نظام القوائم (الأزرار) ---
async def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="btn_king"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="btn_detect")],
        [InlineKeyboardButton("🛡️ الحماية والقفل", callback_data="btn_protect"), InlineKeyboardButton("🎭 الرتب والإدارة", callback_data="btn_ranks")],
        [InlineKeyboardButton("📝 الردود", callback_data="btn_replies"), InlineKeyboardButton("📣 تاك الكل", callback_data="btn_tagall")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "✨ **لوحة تحكم مونوبولي الشاملة** ✨\nإختر القسم المطلوب من الأزرار أدناه:"
    if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    else: await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

# --- معالج الـ Callback (ضغط الأزرار) ---
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    if data == "btn_king":
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {row[0]} 👉👉\n\n🔥🔥 {row[1]} نقطة 🔥🔥\n\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐"
                    back_btn = [[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]
                    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(back_btn))

    elif data == "btn_ranks":
        # قائمة فرعية للرتب
        kb = [[InlineKeyboardButton("رفع مدير", callback_data="rank_manager"), InlineKeyboardButton("رفع أدمن", callback_data="rank_admin")],
              [InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]
        await query.edit_message_text("🎭 إدارة الرتب:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "main_menu":
        await show_main_menu(update)

# --- النشر التلقائي (كل 15 دقيقة) ---
async def auto_post_task(app):
    ads = [
        "📿 سبحان الله وبحمده، سبحان الله العظيم",
        "📜 الحكمة ضالة المؤمن، فحيث وجدها فهو أحق بها",
        "حديث شريف: 'خيركم من تعلم القرآن وعلمه'",
        "💡 لا تجعل اللعبة تلهيك عن ذكر الله وصلاتك"
    ]
    while True:
        await asyncio.sleep(900)
        for chat_id in ALLOWED_GROUPS:
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"📢 نشر تلقائي:\n{random.choice(ads)}")
            except: continue

# --- تشغيل البوت ---
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), monitor_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    
    # بدء مهمة النشر التلقائي
    asyncio.get_event_loop().create_task(auto_post_task(app))
    
    print("🚀 البوت يعمل الآن بكامل طاقته...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
