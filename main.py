import asyncio
import logging
import random
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- الإعدادات الثابتة ---
TOKEN = "8654727197:AAGM3TkKoR_PImPmQ-rSe2lOcITpGMtTkxQ"
OWNER_ID = 5010882230
ALLOWED_GROUPS = [-1002695848824, -1003721123319, -1002052564369]
DATABASE_FILE = "monopoly_pro_v3.db"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. تهيئة قاعدة البيانات ---
async def init_db():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, 
            points INTEGER DEFAULT 0, rank TEXT DEFAULT 'عضو', msgs_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS custom_replies (
            keyword TEXT PRIMARY KEY, response TEXT)""")
        await db.commit()

# --- 2. محرك الصلاحيات ---
async def get_user_rank(user_id):
    if user_id == OWNER_ID: return "مالك أساسي 👑"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT rank FROM users WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "عضو"

async def is_admin(user_id):
    rank = await get_user_rank(user_id)
    return rank in ["مالك أساسي 👑", "مالك", "مدير", "أدمن", "مشرف"]

# --- 3. المعالج الرئيسي للأوامر والرسائل ---
async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id not in ALLOWED_GROUPS:
        if update.effective_chat: await context.bot.leave_chat(update.effective_chat.id)
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # تحديث النقاط وكشف تغيير الاسم
    async with aiosqlite.connect(DATABASE_FILE) as db:
        if context.user_data.get('old_name') and context.user_data['old_name'] != user.full_name:
            await update.message.reply_text(f"⚠️ تغيير اسم!\nID: {user.id}\nالقديم: {context.user_data['old_name']}\nالجديد: {user.full_name}")
        context.user_data['old_name'] = user.full_name

        await db.execute("""INSERT INTO users (user_id, username, full_name, points) 
            VALUES (?, ?, ?, 1) ON CONFLICT(user_id) 
            DO UPDATE SET points=points+1, full_name=excluded.full_name""",
            (user.id, user.username, user.full_name))
        await db.commit()

    # رد "بوت"
    if text == "بوت":
        await update.message.reply_text("🌹 ادارة قروب مونوبولي ترحب بك اهلا وسهلا 🌹\nنحن هنا لكي نجعلك سعيدا لا تجعل اللعبة ان تلهيك عن ذكر الله\n⛔ يمنع اللعب اثناء رفع الاذان واوقات الصلاة ⛔\n⛔يمنع منعا باتا التواصل مع المشرفات⛔\n👈 لاي استفسار يرجى التواصل مع Anas او Sakher 👉")
        return

    # استدعاء منطق الأوامر
    await run_commands_logic(update, context, text)

# --- 4. منطق الأوامر التفصيلي (نصوص + أزرار) ---
async def run_commands_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    admin_status = await is_admin(user_id)

    # أوامر العرض والقوائم
    if text in ["امر", "الاوامر"]:
        await send_main_menu(update)
        return

    # --- نظام الردود (إضافة ومسح) ---
    if admin_status:
        if text.startswith("اضف رد "):
            try:
                parts = text.replace("اضف رد ", "").split("->")
                key, val = parts[0].strip(), parts[1].strip()
                async with aiosqlite.connect(DATABASE_FILE) as db:
                    await db.execute("INSERT OR REPLACE INTO custom_replies VALUES (?,?)", (key, val))
                    await db.commit()
                await update.message.reply_text(f"✅ تم إضافة الرد: {key} -> {val}")
            except: await update.message.reply_text("❌ استخدم: اضف رد الكلمة -> الجواب")
            return
        
        if text.startswith("مسح رد "):
            key = text.replace("مسح رد ", "").strip()
            async with aiosqlite.connect(DATABASE_FILE) as db:
                await db.execute("DELETE FROM custom_replies WHERE keyword=?", (key,))
                await db.commit()
            await update.message.reply_text(f"🗑️ تم مسح الرد على: {key}")
            return

        if text == "مسح الردود":
            async with aiosqlite.connect(DATABASE_FILE) as db:
                await db.execute("DELETE FROM custom_replies")
                await db.commit()
            await update.message.reply_text("💥 تم مسح جميع الردود.")
            return

    # التاكد من الردود التلقائية المضافة
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT response FROM custom_replies WHERE keyword=?", (text,)) as cursor:
            row = await cursor.fetchone()
            if row: await update.message.reply_text(row[0]); return

    # أوامر الإدارة بالرد
    if update.message.reply_to_message and admin_status:
        target = update.message.reply_to_message.from_user
        if target.id == OWNER_ID and text in ["كتم", "حظر", "طرد", "تنزيل"]:
            await update.message.reply_text("🛡️ حماية: لا يمكن المساس بالمالك الأساسي!"); return

        # الرفع والتنزيل
        ranks = {"رفع مشرف": "مشرف", "رفع مدير": "مدير", "رفع ادمن": "أدمن", "رفع مالك": "مالك", "تنزيل الكل": "عضو"}
        if text in ranks:
            new_r = ranks[text]
            async with aiosqlite.connect(DATABASE_FILE) as db:
                await db.execute("UPDATE users SET rank=? WHERE user_id=?", (new_r, target.id))
                await db.commit()
            await update.message.reply_text(f"🎖️ تم تنفيذ {text} لـ {target.first_name}")

        # العقوبات
        if text == "كتم":
            await context.bot.restrict_chat_member(chat_id, target.id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text(f"🔇 تم كتم {target.first_name}")
        elif text == "حظر":
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(f"🚫 تم حظر {target.first_name}")
        elif text == "كشف":
            rank = await get_user_rank(target.id)
            await update.message.reply_text(f"🔍 الاسم: {target.full_name}\n🆔 ID: {target.id}\n🎖️ الرتبة: {rank}")

    # تاك الكل
    if text == "تاك الكل" and admin_status:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT user_id, full_name FROM users") as cursor:
                rows = await cursor.fetchall()
        for i in range(0, len(rows), 10):
            chunk = rows[i:i+10]
            m_text = "📣 نداء للاعضاء:\n" + "\n".join([f"👤 [{m[1]}](tg://user?id={m[0]})" for m in chunk])
            await context.bot.send_message(chat_id=chat_id, text=m_text, parse_mode="Markdown")

# --- 5. نظام القوائم والأزرار ---
async def send_main_menu(update: Update):
    kb = [
        [InlineKeyboardButton("👑 ملك التفاعل", callback_data="king"), InlineKeyboardButton("🔍 كشف", callback_data="detect")],
        [InlineKeyboardButton("🎭 الرتب", callback_data="ranks"), InlineKeyboardButton("🛡️ الحماية", callback_data="protect")],
        [InlineKeyboardButton("🔒 القفل والفتح", callback_data="locks"), InlineKeyboardButton("📝 الردود", callback_data="replies")],
        [InlineKeyboardButton("🔙 اغلاق القائمة", callback_data="close")]
    ]
    msg = "✨ **لوحة تحكم مونوبولي** ✨\nجميع الأزرار مرتبطة بالأوامر النصية:"
    if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu": await send_main_menu(update)
    elif query.data == "close": await query.delete_message()
    elif query.data == "king":
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
        msg = f"👑👑 ملك التفاعل 👑👑\n\n👈👈 {row[0]} 👉👉\n\n🔥🔥 {row[1]} نقطة 🔥🔥\n\n⭐⭐ استمر بالمشاركة يا بطل ⭐⭐" if row else "لا بيانات"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]))
    elif query.data == "replies":
        await query.edit_message_text("📝 **نظام الردود:**\nلإضافة رد اكتب: `اضف رد الكلمة -> الجواب`\nلمسح رد اكتب: `مسح رد الكلمة`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="main_menu")]]), parse_mode="Markdown")

# --- 6. المهام التلقائية (نشر كل 15 دقيقة) ---
async def auto_post(app):
    ads = ["📿 سبحان الله", "🌹 صلّ على النبي", "💡 لا تلهك اللعبة عن الصلاة", "📖 اذكر الله"]
    while True:
        await asyncio.sleep(900)
        for gid in ALLOWED_GROUPS:
            try: await app.bot.send_message(chat_id=gid, text=f"📢 تذكير: {random.choice(ads)}")
            except: continue

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_everything))
    app.add_handler(CallbackQueryHandler(callback_handler))
    loop.create_task(auto_post(app))
    print("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
