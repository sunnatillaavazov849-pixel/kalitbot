"""Plaginlar katalogi va ZIP yuklab olish."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .common import db, esc

router = Router()


def catalog_kb() -> InlineKeyboardMarkup | None:
    rows = [
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']}", callback_data=f"pl:{p['prefix']}")]
        for p in db.plugins()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


async def show_catalog(message: Message):
    kb = catalog_kb()
    if kb is None:
        await message.answer("Hozircha plaginlar yo'q.")
        return
    await message.answer("🛒 <b>Plaginlar</b>\nKeraklisini tanlang:", reply_markup=kb)


def plugin_card(p) -> str:
    desc = f"\n\n{esc(p['description'])}" if p["description"] else ""
    return (
        f"<b>{esc(p['name'])}</b>{desc}\n\n"
        f"💰 Narx: <b>{esc(p['price'])}</b> (bitta kompyuter uchun)\n\n"
        "Yuklab olish bepul, to'lov faollashtirishda qilinadi."
    )


@router.callback_query(F.data == "pls")
async def cb_list(call: CallbackQuery):
    kb = catalog_kb()
    await call.message.edit_text("🛒 <b>Plaginlar</b>\nKeraklisini tanlang:", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("pl:"))
async def cb_plugin(call: CallbackQuery):
    p = db.get_plugin(call.data[3:])
    if p is None or not p["active"]:
        await call.answer("Bu plagin hozir mavjud emas", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Yuklab olish (ZIP)", callback_data=f"dl:{p['prefix']}")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="pls")],
    ])
    await call.message.edit_text(plugin_card(p), reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("dl:"))
async def cb_download(call: CallbackQuery):
    p = db.get_plugin(call.data[3:])
    if p is None or not p["active"]:
        await call.answer("Bu plagin hozir mavjud emas", show_alert=True)
        return
    if not p["zip_file_id"]:
        await call.answer("Fayl hali yuklanmagan. Admin bilan bog'laning: @sunat_aa", show_alert=True)
        return
    await call.message.answer_document(
        p["zip_file_id"],
        caption=(
            f"<b>{esc(p['name'])}</b>\n\n"
            "1) ZIP'ni kompyuterga saqlang va <b>Extract All</b> bilan chiqarib oling.\n"
            "2) Ichidagi <b>.gms</b> faylni CorelDRAW'ning GMS papkasiga qo'ying (<b>O'qing.txt</b> da yozilgan).\n"
            "3) CorelDRAW'da plaginni oching — oynadagi <b>so'rov ID</b>'ni shu botga yuboring.\n\n"
            "Videoli yo'riqnoma: 📖 O'rnatish"
        ),
    )
    await call.answer()
