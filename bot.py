"""Sunat.cc Plaginlar - litsenziya sotish boti."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from handlers import activation, admin, catalog, install, menu, start, transfer
from handlers.common import seed


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # tartib muhim: menyu tugmalari har qanday holatda birinchi ushlanadi, fallback - oxirida
    dp.include_routers(
        menu.router,
        start.router,
        admin.router,
        catalog.router,
        activation.router,
        transfer.router,
        install.router,
        menu.fallback,
    )
    return dp


async def main():
    logging.basicConfig(level=logging.INFO)
    seed()
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await build_dispatcher().start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
