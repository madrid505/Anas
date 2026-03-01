import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN, ALLOWED_GROUPS
from handlers.admin import admin_router
from handlers.user import user_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ربط الأقسام (الأنظمة)
dp.include_router(admin_router)
dp.include_router(user_router)

# --- قائمة الأوامر بالأزرار ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏆 ملك التفاعل", callback_data="king"))
    builder.row(types.InlineKeyboardButton(text="🔒 الأقفال", callback_data="locks"))
    builder.row(types.InlineKeyboardButton(text="🛡️ الإدارة", callback_data="admin"))
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="home"))
    return builder.as_markup()

@dp.message(F.text == "امر")
async def show_menu(message: types.Message):
    await message.answer("🛠️ **أهلاً بك في نظام إدارة مونوبولي:**", reply_markup=main_menu())

# --- المهام التلقائية (نشر أذكار) ---
async def auto_tasks():
    while True:
        await asyncio.sleep(900) # 15 دقيقة
        for chat_id in ALLOWED_GROUPS:
            try:
                await bot.send_message(chat_id, "💡 **تذكير:** لا تنسَ ذكر الله (سبحان الله وبحمده).")
            except: continue

async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(auto_tasks())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
