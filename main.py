import asyncio
import logging
import sys
from os import getenv

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from app.handlers import router as main_router

load_dotenv()
TOKEN = getenv("TOKEN")

dp = Dispatcher()



async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.include_router(main_router)

    await dp.start_polling(bot)



# @dp.message()
# async def start_handler(message: Message):
#     print(message.text)
#     await message.answer(message.text[::-1])




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
