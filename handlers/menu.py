"""Asosiy menyu tugmalari: istalgan holatda ishlaydi (joriy jarayonni bekor qiladi)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from . import activation, catalog, install, start, transfer
from .keyboards import (BTN_ACTIVATE, BTN_CONTACT, BTN_INSTALL, BTN_LEGACY, BTN_MY, BTN_PLUGINS,
                        BTN_TRANSFER, MAIN_KB)

router = Router()


@router.message(F.text == BTN_PLUGINS)
async def m_plugins(message: Message, state: FSMContext):
    await state.clear()
    await catalog.show_catalog(message)


@router.message(F.text == BTN_ACTIVATE)
async def m_activate(message: Message, state: FSMContext):
    await activation.ask_request(message, state)


@router.message(F.text == BTN_MY)
async def m_my(message: Message, state: FSMContext):
    await state.clear()
    await transfer.show_my_licenses(message, state)


@router.message(F.text == BTN_TRANSFER)
async def m_transfer(message: Message, state: FSMContext):
    await state.clear()
    await transfer.start_transfer(message, state)


@router.message(F.text == BTN_INSTALL)
async def m_install(message: Message, state: FSMContext):
    await state.clear()
    await install.show_install(message)


@router.message(F.text == BTN_CONTACT)
async def m_contact(message: Message, state: FSMContext):
    await state.clear()
    await start.show_contacts(message)


@router.message(F.text == BTN_LEGACY)
async def m_legacy(message: Message, state: FSMContext):
    await state.clear()
    await activation.ask_legacy(message, state)


fallback = Router()


@fallback.message()
async def unknown(message: Message):
    await message.answer(
        "Bo'limni tanlang. Plaginni faollashtirish uchun dasturdagi so'rov ID'ni yuboring "
        "(masalan <code>TT-K7QM-3XPA</code>).",
        reply_markup=MAIN_KB,
    )
