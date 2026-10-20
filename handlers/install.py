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
    "2) ZIP ustiga o'ng tugma → <b>Extract All</b> (chiqarib olish). Ichida <b>.gms</b> fayl bor.\n"
    "3) CorelDRAW'ni yoping va <b>.gms</b> ni GMS papkasiga nusxalang. Masalan CorelDRAW 2020 uchun Explorer'ning "
    "manzil qatoriga yozing:\n<code>%APPDATA%\\Corel\\CorelDRAW Graphics Suite 2020\\Draw\\GMS</code>\n"
    "(boshqa versiyada papka nomi boshqacha — videoda ko'rsatilgan).\n"
    "4) CorelDRAW'ni oching va plaginni ishga tushiring — oynada <b>so'rov ID</b> chiqadi "
    "(masalan <code>TT-K7QM-3XPA</code>). Uni nusxalab, shu botga yuboring.\n"
    "5) To'lov chekini yuboring. Admin tasdiqlagach bot kod beradi — uni plagin oynasiga qo'yib <b>OK</b> bosing.\n\n"
    "Boshqa kompyuterga o'tish: CorelDRAW'da <b>Alt+F8 → SunatDezaktiv</b> → chiqqan tasdiq kodini "
    "🔄 <b>Boshqa PC'ga ko'chirish</b> bo'limiga yuboring.\n\n"
    f"Xohlasangiz, plaginni <b>{config.APP_NAME}</b> dasturi orqali ham o'rnatish mumkin (ixtiyoriy)."
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
