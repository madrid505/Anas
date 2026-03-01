# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN, ALLOWED_GROUPS, ADHKAR_INTERVAL
from handlers_admin import admin_router
from handlers_logic import logic_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(admin_router)
dp.include_router(logic_router)

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏆 ملك التفاعل", callback_data="king")
    builder.button(text="🔒 الأقفال", callback_data="locks")
    builder.button(text="🛡️ الإدارة", callback_data="admin")
    builder.button(text="🔄 عودة", callback_data="back")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(F.text == "امر")
async def open_menu(message: types.Message):
    await message.answer("🛠️ **قائمة أوامر مونوبولي:**", reply_markup=main_menu())

async def auto_adhkar():
    while True:
        await asyncio.sleep(ADHKAR_INTERVAL)
        for chat_id in ALLOWED_GROUPS:
            try: await bot.send_message(chat_id, "✨ ذكر الله: سبحان الله وبحمده ✨")
            except: pass

async def main():
    asyncio.create_task(auto_adhkar())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
