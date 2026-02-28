# main.py
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from config import TOKEN, GROUPS_ID, OWNER_ID

# إعداد السجلات لمراقبة البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def start(update, context):
    update.message.reply_text("أهلا! البوت شغال 🚀")

def main():
    if not TOKEN:
        raise ValueError("❌ التوكن غير موجود! تأكد من إعداد متغير البيئة TOKEN")

    # إنشاء تطبيق البوت
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة أوامر بسيطة
    app.add_handler(CommandHandler("start", start))

    # تشغيل البوت
    app.run_polling()

if __name__ == "__main__":
    main()
