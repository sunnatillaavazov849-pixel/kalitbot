"""O'rnatish bo'limi: qadamlar va videolar."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from .common import db, esc
from .keyboards import MAIN_KB

router = Router()

STEPS = (
    "📖 <b>O'rnatish</b>\n\n"
    "1) 🛒 <b>Plaginlar</b> bo'limidan plaginni tanlab, ZIP'ni yuklab oling.\n"
    "2) ZIP ustiga o'ng tugma → <b>Extract All</b> (chiqarib olish).\n"
    f"3) <b>{config.APP_NAME}.exe</b> ni oching. Ko'k \"Windows protected your PC\" oynasi chiqsa: "
    "<b>More info → Run anyway</b>.\n"
    "4) <b>Plagin qo'shish</b> → ZIP'ni tanlang → CorelDRAW versiyangizni belgilang → <b>O'rnatish</b>.\n"
    "5) <b>Plaginlarim</b> → plagin kartochkasidagi <b>so'rov ID</b>'ni nusxalab, botga yuboring.\n"
    "6) To'lov chekini yuboring. Admin tasdiqlagach kelgan kodni dasturga kiriting → <b>Faollashtirish</b>.\n"
    "7) CorelDRAW'ni qayta oching — plagin ishlaydi.\n\n"
    "Boshqa kompyuterga o'tish: 🔄 <b>Boshqa PC'ga ko'chirish</b>."
)


async def show_install(message: Message):
    vids = db.videos()
    kb = None
    if vids:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"▶️ {v['title']}", callback_data=f"vid:{v['id']}")] for v in vids
        ])
    await message.answer(STEPS + ("\n\n🎬 <b>Videolar:</b>" if vids else ""), reply_markup=kb or MAIN_KB)


@router.callback_query(F.data.regexp(r"^vid:\d+$"))
async def cb_video(call: CallbackQuery):
    v = db.get_video(int(call.data[4:]))
    if v is None:
        await call.answer("Video topilmadi", show_alert=True)
        return
    await call.message.answer_video(v["file_id"], caption=f"🎬 {esc(v['title'])}")
    await call.answer()
