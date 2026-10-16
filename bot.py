"""Tez-Tez by Sunat.cc - litsenziya sotish boti."""
import asyncio
import html
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

import db as dbm
from litsenziya import make_password, normalize_machine_code

load_dotenv()


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise SystemExit(f"{name} .env faylida ko'rsatilmagan")
    return value.strip()


BOT_TOKEN = _env("BOT_TOKEN")
LIC_SECRET = _env("LIC_SECRET")
ADMIN_IDS = {int(x) for x in _env("ADMIN_IDS").replace(" ", "").split(",") if x}
PRICE = _env("PRICE", "100 000 so'm")
CARD_NUMBER = _env("CARD_NUMBER", "8600 0000 0000 0000")
CARD_OWNER = _env("CARD_OWNER", "-")
DB_PATH = _env("DB_PATH", "teztez.db")

BRAND = "Tez-Tez by Sunat.cc"
CONTACTS = (
    "📞 <b>Aloqa</b>\n"
    "Telegram: @sunat_aa\n"
    "Instagram: @sunat_cc\n"
    "Tel: +998 33 400 00 43"
)

BTN_BUY = "🛒 Sotib olish"
BTN_REACTIVATE = "🔄 Qayta faollashtirish"
BTN_CONTACT = "📞 Aloqa"

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_BUY)],
        [KeyboardButton(text=BTN_REACTIVATE), KeyboardButton(text=BTN_CONTACT)],
    ],
    resize_keyboard=True,
)
PHONE_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

db = dbm.DB(DB_PATH)
router = Router()


class Order(StatesGroup):
    name = State()
    phone = State()
    code = State()
    receipt = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def order_text(o) -> str:
    kind = "🔄 QAYTA FAOLLASHTIRISH (to'lovsiz)" if o["kind"] == dbm.QAYTA else "🛒 YANGI XARID"
    username = f"@{o['username']}" if o["username"] else "—"
    lines = [
        f"<b>Buyurtma #{o['id']}</b> — {kind}",
        f"👤 Ism: {html.escape(o['name'])}",
        f"📱 Telefon: {html.escape(o['phone'])}",
        f"💬 Telegram: {html.escape(username)} (ID: <code>{o['user_id']}</code>)",
        f"💻 Kompyuter kodi: <code>{o['machine_code']}</code>",
        f"🕒 Sana: {o['created_at']}",
    ]
    if o["kind"] == dbm.QAYTA:
        before = "ha" if db.has_approved(o["user_id"]) else "yo'q"
        lines.append(f"ℹ️ Avval tasdiqlangan xaridi bor: <b>{before}</b>")
    return "\n".join(lines)


def decision_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok:{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no:{order_id}"),
    ]])


# ---------------------------------------------------------------- foydalanuvchi

async def start_order(message: Message, state: FSMContext, kind: str):
    await state.clear()
    await state.update_data(kind=kind)
    await state.set_state(Order.name)
    await message.answer("Ismingizni yozing:", reply_markup=ReplyKeyboardRemove())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        f"Assalomu alaykum! <b>{BRAND}</b> — CorelDRAW uchun taxlash (nesting) plagini.\n\n"
        "Plaginni faollashtirish uchun parol olish bosqichlari:\n"
        "1) ism va telefon raqam\n"
        "2) plagin oynasidagi <b>kompyuter kodi</b>\n"
        "3) to'lov cheki\n\n"
        "Admin to'lovni tasdiqlagach, parol shu yerga yuboriladi.\n"
        f"Bekor qilish: /bekor\n\n{CONTACTS}",
    )
    await start_order(message, state, dbm.YANGI)


@router.message(Command("bekor"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=MAIN_KB)


@router.message(StateFilter(None), F.text == BTN_BUY)
async def btn_buy(message: Message, state: FSMContext):
    await start_order(message, state, dbm.YANGI)


@router.message(StateFilter(None), F.text == BTN_REACTIVATE)
@router.message(Command("qayta"))
async def btn_reactivate(message: Message, state: FSMContext):
    await message.answer(
        "Windows qayta o'rnatilgan yoki tizim diski almashgan bo'lsa, kompyuter kodi "
        "o'zgaradi va yangi parol kerak bo'ladi. Admin tasdiqlasa, yangi parol to'lovsiz beriladi."
    )
    await start_order(message, state, dbm.QAYTA)


@router.message(F.text == BTN_CONTACT)
async def btn_contact(message: Message):
    await message.answer(CONTACTS)


@router.message(Order.name, F.text)
async def got_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 64:
        await message.answer("Ismingizni to'g'ri yozing (2–64 belgi):")
        return
    await state.update_data(name=name)
    await state.set_state(Order.phone)
    await message.answer(
        "Telefon raqamingizni yuboring — pastdagi tugmani bosing yoki yozing:",
        reply_markup=PHONE_KB,
    )


@router.message(Order.phone, F.contact)
async def got_contact(message: Message, state: FSMContext):
    await save_phone(message, state, message.contact.phone_number)


@router.message(Order.phone, F.text)
async def got_phone_text(message: Message, state: FSMContext):
    digits = "".join(ch for ch in message.text if ch.isdigit())
    if not 9 <= len(digits) <= 15:
        await message.answer("Raqam noto'g'ri. Masalan: +998 90 123 45 67", reply_markup=PHONE_KB)
        return
    await save_phone(message, state, message.text.strip())


async def save_phone(message: Message, state: FSMContext, phone: str):
    if not phone.startswith("+") and phone[:1].isdigit():
        phone = "+" + phone
    await state.update_data(phone=phone)
    await state.set_state(Order.code)
    await message.answer(
        "Endi <b>kompyuter kodini</b> yuboring.\n"
        "U CorelDRAW'dagi Tez-Tez plagini oynasida ko'rinadi, masalan: <code>K7QM-3XPA</code>",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Order.code, F.text)
async def got_code(message: Message, state: FSMContext):
    code = normalize_machine_code(message.text)
    if code is None:
        await message.answer(
            "Kompyuter kodi noto'g'ri. U 8 ta belgidan iborat, masalan <code>K7QM-3XPA</code>.\n"
            "Plagin oynasidagi kodni aynan ko'chirib yuboring:"
        )
        return
    await state.update_data(code=code)
    data = await state.get_data()
    if data.get("kind") == dbm.QAYTA:
        await submit(message, state, receipt=None)
        return
    await state.set_state(Order.receipt)
    await message.answer(
        f"💻 Kompyuter kodi: <code>{code}</code>\n\n"
        f"💰 Narx: <b>{html.escape(PRICE)}</b>\n"
        f"💳 Karta: <code>{html.escape(CARD_NUMBER)}</code>\n"
        f"👤 Karta egasi: {html.escape(CARD_OWNER)}\n\n"
        "To'lovni amalga oshirib, <b>chek rasmini</b> shu yerga yuboring."
    )


@router.message(Order.receipt, F.photo)
async def got_receipt_photo(message: Message, state: FSMContext):
    await submit(message, state, receipt="photo:" + message.photo[-1].file_id)


@router.message(Order.receipt, F.document)
async def got_receipt_doc(message: Message, state: FSMContext):
    mime = message.document.mime_type or ""
    if not (mime.startswith("image/") or mime == "application/pdf"):
        await message.answer("Iltimos, chekni rasm (yoki PDF) ko'rinishida yuboring.")
        return
    await submit(message, state, receipt="doc:" + message.document.file_id)


@router.message(StateFilter(Order.name, Order.phone, Order.code, Order.receipt))
async def wrong_input(message: Message, state: FSMContext):
    hints = {
        Order.name.state: "Ismingizni matn ko'rinishida yozing.",
        Order.phone.state: "Telefon raqamingizni yuboring.",
        Order.code.state: "Kompyuter kodini matn ko'rinishida yuboring.",
        Order.receipt.state: "To'lov chekini rasm ko'rinishida yuboring.",
    }
    await message.answer(hints.get(await state.get_state(), "") + "\nBekor qilish: /bekor")


async def submit(message: Message, state: FSMContext, receipt: str | None):
    data = await state.get_data()
    await state.clear()
    user = message.from_user
    order_id = db.add_order(
        user.id, user.username, data["name"], data["phone"], data["code"],
        data.get("kind", dbm.YANGI), receipt,
    )
    o = db.get(order_id)
    text = order_text(o)
    kb = decision_kb(order_id)
    for admin_id in ADMIN_IDS:
        try:
            if receipt and receipt.startswith("photo:"):
                await message.bot.send_photo(admin_id, receipt[6:], caption=text, reply_markup=kb)
            elif receipt and receipt.startswith("doc:"):
                await message.bot.send_document(admin_id, receipt[4:], caption=text, reply_markup=kb)
            else:
                await message.bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            logging.exception("Adminga (%s) yuborib bo'lmadi", admin_id)
    await message.answer(
        f"✅ So'rovingiz qabul qilindi (#{order_id}).\n"
        "Admin tekshirgach, parol shu yerga yuboriladi. Iltimos, kuting.",
        reply_markup=MAIN_KB,
    )


# ---------------------------------------------------------------- admin

@router.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def on_decision(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q", show_alert=True)
        return
    action, raw_id = call.data.split(":")
    order_id = int(raw_id)
    o = db.get(order_id)
    if o is None:
        await call.answer("Buyurtma topilmadi", show_alert=True)
        return

    if action == "ok":
        password = make_password(o["machine_code"], LIC_SECRET)
        if not db.decide(order_id, dbm.TASDIQLANDI, password):
            await call.answer(f"Bu buyurtma allaqachon ko'rib chiqilgan: {o['status']}", show_alert=True)
            return
        result = f"\n\n✅ <b>TASDIQLANDI</b>\n🔑 Parol: <code>{password}</code>"
        user_text = (
            "✅ To'lovingiz tasdiqlandi!\n\n"
            f"💻 Kompyuter kodi: <code>{o['machine_code']}</code>\n"
            f"🔑 Parol: <code>{password}</code>\n\n"
            "Parolni CorelDRAW'dagi Tez-Tez plagini oynasidagi <b>\"Kodni kiriting\"</b> "
            "maydoniga kiriting.\n"
            "⚠️ Parol faqat shu kompyuterda ishlaydi.\n\n"
            f"Rahmat! {BRAND}\n\n{CONTACTS}"
        )
    else:
        if not db.decide(order_id, dbm.RAD_ETILDI):
            await call.answer(f"Bu buyurtma allaqachon ko'rib chiqilgan: {o['status']}", show_alert=True)
            return
        result = "\n\n❌ <b>RAD ETILDI</b>"
        user_text = (
            "❌ To'lov tasdiqlanmadi.\n"
            f"Savollar bo'lsa, admin bilan bog'laning.\n\n{CONTACTS}"
        )

    try:
        await call.bot.send_message(o["user_id"], user_text, reply_markup=MAIN_KB)
        delivered = ""
    except Exception:
        logging.exception("Foydalanuvchiga (%s) yuborib bo'lmadi", o["user_id"])
        delivered = "\n⚠️ Foydalanuvchiga yuborib bo'lmadi (botni bloklagan bo'lishi mumkin)."

    new_text = order_text(db.get(order_id)) + result + delivered
    try:
        if call.message.photo or call.message.document:
            await call.message.edit_caption(caption=new_text, reply_markup=None)
        else:
            await call.message.edit_text(new_text, reply_markup=None)
    except Exception:
        logging.exception("Admin xabarini yangilab bo'lmadi")
    await call.answer("Bajarildi")


@router.message(Command("royxat"))
async def cmd_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = db.recent(30)
    if not rows:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return
    icons = {dbm.KUTILMOQDA: "⏳", dbm.TASDIQLANDI: "✅", dbm.RAD_ETILDI: "❌"}
    s = db.stats()
    chunks = [
        f"<b>Oxirgi {len(rows)} ta buyurtma</b>\n"
        f"⏳ {s.get(dbm.KUTILMOQDA, 0)}  ✅ {s.get(dbm.TASDIQLANDI, 0)}  "
        f"❌ {s.get(dbm.RAD_ETILDI, 0)}\n"
    ]
    for o in rows:
        line = (
            f"\n{icons.get(o['status'], '•')} #{o['id']} {o['created_at']}"
            f"{' 🔄' if o['kind'] == dbm.QAYTA else ''}\n"
            f"   {html.escape(o['name'])}, {html.escape(o['phone'])}\n"
            f"   <code>{o['machine_code']}</code>"
            + (f" → <code>{o['password']}</code>" if o["password"] else "")
            + "\n"
        )
        if len(chunks[-1]) + len(line) > 4000:
            chunks.append("")
        chunks[-1] += line
    for chunk in chunks:
        await message.answer(chunk)


@router.message(Command("parol"))
async def cmd_password(message: Message):
    """Admin uchun: /parol K7QM-3XPA - buyurtmasiz parol hisoblash."""
    if not is_admin(message.from_user.id):
        return
    parts = (message.text or "").split(maxsplit=1)
    code = normalize_machine_code(parts[1]) if len(parts) > 1 else None
    if code is None:
        await message.answer("Foydalanish: <code>/parol K7QM-3XPA</code>")
        return
    await message.answer(f"💻 <code>{code}</code>\n🔑 <code>{make_password(code, LIC_SECRET)}</code>")


@router.message()
async def fallback(message: Message):
    await message.answer("Parol olish uchun «🛒 Sotib olish» tugmasini bosing.", reply_markup=MAIN_KB)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
