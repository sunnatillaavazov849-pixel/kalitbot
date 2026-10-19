from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_PLUGINS = "🛒 Plaginlar"
BTN_ACTIVATE = "🔑 Faollashtirish"
BTN_MY = "📂 Litsenziyalarim"
BTN_TRANSFER = "🔄 Boshqa PC'ga ko'chirish"
BTN_INSTALL = "📖 O'rnatish"
BTN_CONTACT = "📞 Aloqa"
BTN_LEGACY = "♻️ Eski litsenziya"

MENU_BUTTONS = {BTN_PLUGINS, BTN_ACTIVATE, BTN_MY, BTN_TRANSFER, BTN_INSTALL, BTN_CONTACT, BTN_LEGACY}

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PLUGINS), KeyboardButton(text=BTN_ACTIVATE)],
        [KeyboardButton(text=BTN_MY), KeyboardButton(text=BTN_TRANSFER)],
        [KeyboardButton(text=BTN_INSTALL), KeyboardButton(text=BTN_CONTACT)],
        [KeyboardButton(text=BTN_LEGACY)],
    ],
    resize_keyboard=True,
)

PHONE_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)
