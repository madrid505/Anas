import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import TOKEN, OWNER_ID, ALLOWED_GROUPS, PORT, WEBHOOK_URL
from database import cursor, conn

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =============================
# 🔐 حماية القروبات
# =============================

async def group_protection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        if update.effective_chat.id not in ALLOWED_GROUPS:
            await update.message.reply_text("❌ هذا البوت غير مسموح له بالعمل هنا.")
            await context.bot.leave_chat(update.effective_chat.id)

# =============================
# 👑 حماية المالك الأساسي
# =============================

async def owner_protection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        if target_id == OWNER_ID:
            await update.message.reply_text("⛔ لا يمكن تنفيذ أي إجراء على المالك الأساسي.")
            return

# =============================
# 👑 عداد ملك التفاعل
# =============================

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    group_id = update.effective_chat.id
    user_id = update.effective_user.id

    cursor.execute("""
    INSERT INTO messages (group_id, user_id, count)
    VALUES (?, ?, 1)
    ON CONFLICT(group_id, user_id)
    DO UPDATE SET count = count + 1
    """, (group_id, user_id))

    conn.commit()

# =============================
# 🚀 تشغيل التطبيق
# =============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, group_protection), group=0)
    app.add_handler(MessageHandler(filters.ALL, owner_protection), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages), group=2)

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
