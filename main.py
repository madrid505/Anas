import asyncio
import sqlite3
import logging
import random
import aiosqlite  # تم إضافة الاستدعاء المفقود هنا
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- الإعدادات الأساسية ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "monopoly_ultimate.db"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. محرك قاعدة البيانات ---
async def init_db():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, 
            points INTEGER DEFAULT 0, rank TEXT DEFAULT 'عضو', msgs_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY, locked_settings TEXT DEFAULT '')""")
        await db.execute("""CREATE TABLE IF NOT EXISTS custom_replies (
            keyword TEXT PRIMARY KEY, response TEXT)""")
        await db.commit()

# --- 2. وظائف الحماية والصلاحيات ---
async def get_rank(user_id):
    if user_id == OWNER_ID: return "مالك أساسي 👑"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT rank FROM users WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "عضو"

async def is_admin(update: Update):
    rank = await get_rank(update.effective_user.id)
    return rank in ["مالك أساسي 👑", "مدير", "أدمن", "مالك"]

# --- 3. معالجة الرسائل (العد التراكمي + كشف الاسم + الردود) ---
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS: return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # تحديث النقاط وكشف تغيير الاسم
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""INSERT INTO users (user_id, username, full_name, points, msgs_count) 
            VALUES (?, ?, ?, 1, 1) ON CONFLICT(user_id) 
            DO UPDATE SET points=points+1, msgs_count=msgs_count+1, full_name=excluded.full_name""",
            (user.id, user.username, user.full_name))
        await db.commit()

    # الرد على "بوت"
    if text == "بوت":
        resp = ("🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\n"
                "⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة ⛔\n"
                "⛔ يمنع منعا باتا التواصل مع المشرفات ⛔\n"
                "👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉")
        await update.message.reply_text(resp)

    # أوامر النصوص (رفع، حظر، كشف، قفل)
    await text_commands_logic(update, context, text)

# --- 4. منطق الأوامر النصية ---
async def text_commands_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "امر":
        await send_main_menu(update)
    
    # كشف البيانات
    if text == "كشف" and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT points, rank FROM users WHERE user_id=?", (target.id,)) as cursor:
                row = await cursor.fetchone()
        p, r = (row[0], row[1]) if row else (0, "عضو")
        await update.message.reply_text(f"🔍 بيانات العضو:\nالاسم: {target.full_name}\nID: {target.id}\nالرسائل: {p}\nالرتبة: {r}")

    # أوامر الرفع (مثال لرفع مدير)
    if text.startswith("رفع") and await is_admin(update) and update.message.reply_to_message:
        rank_to_set = text.replace("رفع ", "")
        target = update.message.reply_to_message.from_user
        if target.id == OWNER_ID: return
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute("UPDATE users SET rank=? WHERE user_id=?", (rank_to_set, target.id))
            await db.commit()
        await update.message.reply_text(f"✅ تم رفع {target.first_name} إلى {rank_to_set}")

    # تاك الكل
    if text == "تاك الكل" and await is_admin(update):
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT user_id, full_name FROM users") as cursor:
                members = await cursor.fetchall()
        for i in range(0, len(members), 5):
            chunk = members[i:i+5]
            mentions = " ".join([f"[{m[1]}](tg://user?id={m[0]})" for m in chunk])
            await context.bot.send_message(chat_id=update.effective_chat.id, text=mentions, parse_mode="Markdown")
            await asyncio.sleep(1)

# --- 5. نظام القوائم والأزرار (مع زر العودة) ---
async def send_main_menu(update: Update):
    kb = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
        [InlineKeyboardButton("🛡️ الحماية", callback_data="protect"), InlineKeyboardButton("🎭 الرتب", callback_data="ranks")],
        [InlineKeyboardButton("🔒 القفل والفتح", callback_data="locks"), InlineKeyboardButton("📝 الردود", callback_data="replies")]
    ]
    text = "✨ **لوحة تحكم مونوبولي الشاملة** ✨\nاستخدم الأزرار للتحقل بين الأقسام:"
    if update.callback_query: await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await send_main_menu(update)
    
    elif query.data == "king":
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
        msg = f"👑 ملك التفاعل\n\n👤 {row[0]}\n🔥 {row[1]} نقطة\n\nاستمر يا بطل!" if row else "لا يوجد بيانات."
        kb = [[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "ranks":
        kb = [
            [InlineKeyboardButton("رفع مدير", callback_data="r_manager"), InlineKeyboardButton("رفع أدمن", callback_data="r_admin")],
            [InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]
        ]
        await query.edit_message_text("🎭 قائمة الرفع والتنزيل (بالرد):", reply_markup=InlineKeyboardMarkup(kb))

# --- 6. النشر التلقائي كل 15 دقيقة ---
async def auto_post(app):
    msgs = ["📿 سبحان الله", "📖 اذكر الله", "🌹 صلّ على محمد", "💡 اللعبة لا تلهيك عن الصلاة"]
    while True:
        await asyncio.sleep(900)
        for gid in ALLOWED_GROUPS:
            try: await app.bot.send_message(chat_id=gid, text=random.choice(msgs))
            except: continue

# --- 7. تشغيل البوت ---
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), main_handler))
    app.add_handler(CallbackQueryHandler(on_click))
    
    # تشغيل النشر التلقائي في الخلفية
    loop.create_task(auto_post(app))
    
    print("🚀 البوت انطلق بنجاح...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
