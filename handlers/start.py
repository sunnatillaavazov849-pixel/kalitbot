"""/start, ro'yxatdan o'tish (ism + telefon), aloqa."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

import config
from .common import db
from .keyboards import MAIN_KB, PHONE_KB

router = Router()


class Reg(StatesGroup):
    name = State()
    phone = State()


WELCOME = (
    f"Assalomu alaykum! <b>{config.BRAND}</b> — CorelDRAW uchun plaginlar.\n\n"
    "<b>Qanday ishlaydi:</b>\n"
    "1) 🛒 <b>Plaginlar</b> bo'limidan keraklisini tanlab, ZIP faylni yuklab olasiz.\n"
    "2) Plaginni CorelDRAW'ga qo'yasiz va ochasiz — oynada <b>so'rov ID</b> chiqadi.\n"
    "3) So'rov ID'ni shu yerga yuborasiz va to'lov qilasiz.\n"
    "4) Admin tasdiqlagach, bot <b>faollashtirish kodi</b>ni beradi — uni plagin oynasiga kiritasiz.\n\n"
    "Batafsil va videolar: 📖 <b>O'rnatish</b>."
)


async def require_user(message: Message, state: FSMContext, pending: str | None = None):
    """Ro'yxatdan o'tgan bo'lsa user qatorini qaytaradi, aks holda ro'yxatdan o'tkazishni boshlaydi.
    `pending` — ro'yxatdan keyin davom ettiriladigan so'rov ID."""
    user = db.get_user(message.chat.id)
    if user is not None:
        return user
    await state.clear()
    await state.update_data(pending=pending)
    await state.set_state(Reg.name)
    await message.answer(
        "Avval qisqa ro'yxatdan o'tamiz.\nIsmingizni yozing:", reply_markup=ReplyKeyboardRemove()
    )
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME)
    if db.get_user(message.from_user.id) is None:
        await require_user(message, state)
    else:
        await message.answer("Bo'limni tanlang:", reply_markup=MAIN_KB)


@router.message(Command("bekor"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=MAIN_KB)


@router.message(Reg.name, F.text)
async def got_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 64 or name.startswith("/"):
        await message.answer("Ismingizni to'g'ri yozing (2–64 belgi):")
        return
    await state.update_data(name=name)
    await state.set_state(Reg.phone)
    await message.answer(
        "Telefon raqamingizni yuboring — pastdagi tugmani bosing yoki yozing:", reply_markup=PHONE_KB
    )


@router.message(Reg.phone, F.contact)
async def got_contact(message: Message, state: FSMContext):
    await save_phone(message, state, message.contact.phone_number)


@router.message(Reg.phone, F.text)
async def got_phone_text(message: Message, state: FSMContext):
    digits = "".join(ch for ch in message.text if ch.isdigit())
    if not 9 <= len(digits) <= 15:
        await message.answer("Raqam noto'g'ri. Masalan: +998 90 123 45 67", reply_markup=PHONE_KB)
        return
    await save_phone(message, state, message.text.strip())


@router.message(Reg.name)
@router.message(Reg.phone)
async def reg_wrong(message: Message):
    await message.answer("Iltimos, so'ralgan ma'lumotni yuboring. Bekor qilish: /bekor")


async def save_phone(message: Message, state: FSMContext, phone: str):
    if not phone.startswith("+") and phone[:1].isdigit():
        phone = "+" + phone
    data = await state.get_data()
    await state.clear()
    db.save_user(message.from_user.id, message.from_user.username, data["name"], phone)
    await message.answer("✅ Ro'yxatdan o'tdingiz.", reply_markup=MAIN_KB)
    pending = data.get("pending")
    if pending:
        from . import activation  # aylanma importdan qochish uchun
        await activation.handle_request_text(message, state, pending)


async def show_contacts(message: Message):
    await message.answer(config.CONTACTS, reply_markup=MAIN_KB)
