import asyncio
import sqlite3
import logging
import random
import aiosqlite
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- الإعدادات الثابتة (حسب توجيهاتك) ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "monopoly_misk.db"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. إدارة قاعدة البيانات ---
async def init_db():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, 
            points INTEGER DEFAULT 0, rank TEXT DEFAULT 'عضو', msgs_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS custom_replies (
            keyword TEXT PRIMARY KEY, response TEXT)""")
        await db.commit()

# --- 2. التحقق من الصلاحيات وحماية المالك ---
async def get_user_rank(user_id):
    if user_id == OWNER_ID: return "المالك الأساسي 👑"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT rank FROM users WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "عضو"

async def is_admin(update: Update):
    rank = await get_user_rank(update.effective_user.id)
    return rank in ["المالك الأساسي 👑", "مدير", "أدمن", "مالك", "مشرف"]

# --- 3. المعالج الرئيسي (رسائل + أوامر نصية) ---
async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS: return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # تحديث النقاط (العد التراكمي)
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""INSERT INTO users (user_id, username, full_name, points) 
            VALUES (?, ?, ?, 1) ON CONFLICT(user_id) 
            DO UPDATE SET points=points+1, full_name=excluded.full_name""",
            (user.id, user.username, user.full_name))
        await db.commit()

    # الردود الملكية
    if text == "بوت":
        await update.message.reply_text("🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\nنحن هنا لكي نجعلك سعيدا لا تجعل اللعبة ان تلهيك عن ذكر الله\n⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة ⛔\n⛔يمنع منعا باتا التواصل مع المشرفات⛔\n👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉")
        return

    # أوامر القفل والفتح
    if text == "قفل الروابط" and await is_admin(update):
        await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True, can_add_web_page_previews=False))
        await update.message.reply_text("🚫 تم قفل الروابط.")
    elif text == "فتح الروابط" and await is_admin(update):
        await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text("✅ تم فتح الروابط.")

    # أوامر الإدارة بالرد (كشف، كتم، رفع)
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if text == "كشف":
            rank = await get_user_rank(target.id)
            await update.message.reply_text(f"🔍 بيانات العضو:\nالاسم: {target.full_name}\nID: {target.id}\nالرتبة: {rank}")
        
        if text == "كتم" and await is_admin(update):
            if target.id == OWNER_ID: return await update.message.reply_text("❌ لا يمكن كتم المالك!")
            await context.bot.restrict_chat_member(chat_id, target.id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text(f"🔇 تم كتم {target.first_name}")

        if text.startswith("رفع") and await is_admin(update):
            new_rank = text.replace("رفع ", "")
            async with aiosqlite.connect(DATABASE_FILE) as db:
                await db.execute("UPDATE users SET rank=? WHERE user_id=?", (new_rank, target.id))
                await db.commit()
            await update.message.reply_text(f"🎖️ تم رفع {target.first_name} إلى رتبة {new_rank}")

    # لوحة الأوامر
    if text == "امر":
        await send_main_menu(update)

    # تاك الكل
    if text == "تاك الكل" and await is_admin(update):
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT user_id, full_name FROM users") as cursor:
                rows = await cursor.fetchall()
        for i in range(0, len(rows), 5):
            chunk = rows[i:i+5]
            mentions = " ".join([f"[{m[1]}](tg://user?id={m[0]})" for m in chunk])
            await context.bot.send_message(chat_id=chat_id, text=mentions, parse_mode="Markdown")
            await asyncio.sleep(1)

# --- 4. نظام القوائم والأزرار مع زر العودة ---
async def send_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king"), InlineKeyboardButton("🔍 كشف البيانات", callback_data="detect")],
        [InlineKeyboardButton("🛡️ الحماية", callback_data="protect"), InlineKeyboardButton("🎭 الرتب", callback_data="ranks")],
        [InlineKeyboardButton("🔒 القفل والفتح", callback_data="locks"), InlineKeyboardButton("📝 الردود", callback_data="replies")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    msg = "✨ **لوحة تحكم مونوبولي الشاملة** ✨\nاستخدم الأزرار للتنقل (يوجد زر عودة في كل قائمة):"
    if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=markup, parse_mode="Markdown")
    else: await update.message.reply_text(msg, reply_markup=markup, parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await send_main_menu(update)
    
    elif query.data == "king":
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
        msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {row[0]} 👉👉\n\n🔥🔥 {row[1]} نقطة 🔥🔥\n\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐" if row else "لا يوجد بيانات بعد."
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]))

    elif query.data == "ranks":
        kb = [[InlineKeyboardButton("رفع مدير", callback_data="r_manager"), InlineKeyboardButton("رفع أدمن", callback_data="r_admin")],
              [InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]
        await query.edit_message_text("🎭 إدارة الرتب (استخدم الرفع نصياً بالرد حالياً):", reply_markup=InlineKeyboardMarkup(kb))

# --- 5. النشر التلقائي كل 15 دقيقة ---
async def auto_post_task(app):
    msgs = ["📿 سبحان الله وبحمده", "📖 ألا بذكر الله تطمئن القلوب", "🌹 صلّ على النبي", "💡 اللعبة وسيلة تسلية، فلا تلهيك عن صلاتك"]
    while True:
        await asyncio.sleep(900)
        for gid in ALLOWED_GROUPS:
            try: await app.bot.send_message(chat_id=gid, text=f"📢 تذكير:\n{random.choice(msgs)}")
            except: continue

# --- 6. تشغيل السيرفر ---
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_everything))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    loop.create_task(auto_post_task(app))
    
    print("🚀 Misk-bot is Running perfectly on Northflank...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
