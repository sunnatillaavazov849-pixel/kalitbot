"""Handlerlar uchun umumiy narsalar."""
import html
import logging

from aiogram import Bot

import config
import db as dbm

db = dbm.DB(config.DB_PATH)

esc = html.escape


def seed():
    """Birinchi ishga tushishda Tez-Tez plaginini mavjud kalit bilan qo'shadi."""
    if db.get_plugin("TT") is None:
        db.add_plugin(
            "TT", "Tez-Tez", config.PRICE,
            "CorelDRAW uchun taxlash (nesting) plagini.",
            secret=config.LIC_SECRET,
        )


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def notify_admins(bot: Bot, text: str, **kwargs):
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, **kwargs)
        except Exception:
            logging.exception("Adminga (%s) yuborib bo'lmadi", admin_id)


def plugin_name(prefix: str) -> str:
    p = db.get_plugin(prefix)
    return p["name"] if p else prefix


def user_label(user_id: int) -> str:
    u = db.get_user(user_id)
    if u is None:
        return f"ID <code>{user_id}</code>"
    uname = f" @{esc(u['username'])}" if u["username"] else ""
    return f"{esc(u['name'])}, {esc(u['phone'])}{uname} (ID <code>{user_id}</code>)"
