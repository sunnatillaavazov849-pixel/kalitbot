"""Litsenziyalarim va boshqa kompyuterga ko'chirish (dezaktivatsiya)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
import db as dbm
from litsenziya import deact_confirm, normalize_machine_code
from .common import db, esc, notify_admins, plugin_name, user_label
from .keyboards import MAIN_KB, MENU_BUTTONS
from .start import require_user

router = Router()


class Tr(StatesGroup):
    reason = State()
    confirm = State()


STATUS = {dbm.FAOL: "🟢 Faol", dbm.BOSH: "⚪️ Bo'sh (yangi PC'ga o'tkazish mumkin)", dbm.BLOKLANGAN: "⛔ Bloklangan"}

RULES = (
    "🔄 <b>Boshqa kompyuterga ko'chirish</b>\n\n"
    "Windows qayta o'rnatilsa yoki kompyuter almashsa, litsenziyangiz yo'qolmaydi: uni eski kompyuterda "
    "o'chirib (dezaktiv), yangisida to'lovsiz yoqasiz. Litsenziya bir vaqtda faqat <b>bitta</b> kompyuterda ishlaydi.\n\n"
    "<b>Qoidalar:</b>\n"
    "• kuniga <b>1 marta</b> ko'chirish mumkin;\n"
    f"• jami <b>{dbm.MAX_DEACT} marta</b>; undan keyin litsenziya bloklanadi.\n"
)


async def show_my_licenses(message: Message, state: FSMContext):
    user = await require_user(message, state)
    if user is None:
        return
    lics = db.user_licenses(user["user_id"])
    if not lics:
        await message.answer("Sizda hali litsenziya yo'q. 🛒 Plaginlar bo'limidan boshlang.", reply_markup=MAIN_KB)
        return
    lines = ["📂 <b>Litsenziyalarim</b>"]
    for l in lics:
        left = max(dbm.MAX_DEACT - l["deact_count"], 0)
        lines.append(f"\n<b>#{l['id']} · {esc(plugin_name(l['plugin']))}</b>\n{STATUS.get(l['status'], l['status'])}")
        if l["status"] == dbm.FAOL:
            lines.append(f"💻 Kompyuter: <code>{l['mid']}</code>\n🔑 Kod: <code>{l['code']}</code>")
        if l["status"] != dbm.BLOKLANGAN:
            lines.append(f"🔄 Qolgan ko'chirishlar: {left}")
    await message.answer("\n".join(lines), reply_markup=MAIN_KB)


async def start_transfer(message: Message, state: FSMContext):
    user = await require_user(message, state)
    if user is None:
        return
    lics = [l for l in db.user_licenses(user["user_id"]) if l["status"] == dbm.FAOL]
    if not lics:
        await message.answer(RULES + "\nSizda hozir faol litsenziya yo'q.", reply_markup=MAIN_KB)
        return
    rows = [[InlineKeyboardButton(text=f"{plugin_name(l['plugin'])} · {l['mid']}", callback_data=f"tr:{l['id']}")]
            for l in lics]
    await message.answer(RULES + "\nQaysi litsenziyani ko'chiramiz?",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.regexp(r"^tr:\d+$"))
async def cb_pick(call: CallbackQuery, state: FSMContext):
    lic = db.get_license(int(call.data[3:]))
    if lic is None or lic["user_id"] != call.from_user.id:
        await call.answer("Litsenziya topilmadi", show_alert=True)
        return
    await call.answer()
    problem = db.deact_check(lic)
    if problem == "holat":
        await call.message.answer("Bu litsenziya hozir faol emas.", reply_markup=MAIN_KB)
        return
    if problem == "bugun":
        await call.message.answer("Bugun bu litsenziya allaqachon ko'chirilgan. Ertaga qayta urinib ko'ring.",
                                  reply_markup=MAIN_KB)
        return
    if problem == "limit":
        db.block_license(lic["id"])
        await call.message.answer(
            f"⛔ Litsenziya bloklandi: ko'chirishlar soni {dbm.MAX_DEACT} tadan oshdi.\n"
            "Admin bilan bog'laning (@sunat_aa) yoki yangi litsenziya sotib oling.",
            reply_markup=MAIN_KB,
        )
        await notify_admins(
            call.bot,
            f"⛔ Litsenziya #{lic['id']} bloklandi (ko'chirish limiti)\n"
            f"🧩 {esc(plugin_name(lic['plugin']))} · 💻 <code>{lic['mid']}</code>\n👤 {user_label(lic['user_id'])}\n"
            f"Blokdan chiqarish: /blokdan_chiqar {lic['id']}",
        )
        return
    await state.clear()
    await state.update_data(lic_id=lic["id"])
    await state.set_state(Tr.reason)
    left = dbm.MAX_DEACT - lic["deact_count"]
    await call.message.answer(
        f"🧩 {esc(plugin_name(lic['plugin']))} · 💻 <code>{lic['mid']}</code>\n"
        f"Qolgan ko'chirishlar: <b>{left}</b>\n\n"
        "<b>Nima bo'ldi?</b> Qisqacha yozing (masalan: <i>Windows qayta o'rnatildi</i>, "
        "<i>yangi kompyuter oldim</i>).\nBekor qilish: /bekor"
    )


NOCODE_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="💥 Eski kompyuter ishlamayapti (kod yo'q)", callback_data="trnocode")
]])


@router.message(Tr.reason, F.text, ~F.text.in_(MENU_BUTTONS))
async def got_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    if len(reason) < 3 or reason.startswith("/"):
        await message.answer("Iltimos, sababni bir necha so'z bilan yozing:")
        return
    await state.update_data(reason=reason[:500])
    await state.set_state(Tr.confirm)
    await message.answer(
        "Endi <b>eski kompyuterda</b>:\n"
        f"1) <b>{config.APP_NAME}</b> dasturini oching → <b>Plaginlarim</b>;\n"
        "2) plagin kartochkasida <b>Dezaktiv qilish</b> ni bosing;\n"
        "3) dastur ko'rsatgan <b>tasdiq kodini</b> (masalan <code>AB3K-7QMX</code>) shu yerga yuboring.\n\n"
        "Eski kompyuter umuman ishlamasa (Windows uchgan, disk buzilgan), pastdagi tugmani bosing.",
        reply_markup=NOCODE_KB,
    )


@router.message(Tr.confirm, F.text, ~F.text.in_(MENU_BUTTONS))
async def got_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    lic = db.get_license(data["lic_id"])
    code = normalize_machine_code(message.text)
    if lic is None or lic["status"] != dbm.FAOL:
        await state.clear()
        await message.answer("Litsenziya holati o'zgargan. Qaytadan urinib ko'ring.", reply_markup=MAIN_KB)
        return
    if code is None or code != deact_confirm(lic["code"], lic["mid"]):
        await message.answer(
            "Tasdiq kodi noto'g'ri. Dasturdagi kodni aynan ko'chirib yuboring yoki pastdagi tugmani bosing.",
            reply_markup=NOCODE_KB,
        )
        return
    await finish(message, state, confirmed=True)


@router.callback_query(Tr.confirm, F.data == "trnocode")
async def cb_nocode(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await finish(call.message, state, confirmed=False)


async def finish(message: Message, state: FSMContext, confirmed: bool):
    data = await state.get_data()
    await state.clear()
    lic = db.get_license(data["lic_id"])
    old_mid = lic["mid"] if lic else None
    if lic is None or not db.deactivate(lic["id"], data["reason"], confirmed):
        await message.answer("Ko'chirib bo'lmadi: litsenziya holati o'zgargan yoki bugungi limit tugagan.",
                             reply_markup=MAIN_KB)
        return
    lic = db.get_license(lic["id"])
    left = dbm.MAX_DEACT - lic["deact_count"]
    warn = "\n⚠️ Bu oxirgi ko'chirish edi. Keyingi urinishda litsenziya bloklanadi." if left == 0 else ""
    await message.answer(
        "✅ Litsenziya eski kompyuterdan bo'shatildi.\n\n"
        f"Yangi kompyuterda <b>{config.APP_NAME}</b> dasturini o'rnating, plaginni qo'shing va yangi "
        "<b>so'rov ID</b>'ni shu yerga yuboring — kod <b>to'lovsiz</b> beriladi.\n\n"
        f"Qolgan ko'chirishlar: <b>{left}</b>{warn}",
        reply_markup=MAIN_KB,
    )
    await notify_admins(
        message.bot,
        f"🔄 Litsenziya #{lic['id']} bo'shatildi ({lic['deact_count']}/{dbm.MAX_DEACT})\n"
        f"🧩 {esc(plugin_name(lic['plugin']))} · eski 💻 <code>{old_mid}</code>\n"
        f"👤 {user_label(lic['user_id'])}\n"
        f"📝 Sabab: {esc(data['reason'])}\n"
        f"{'✅ Tasdiq kodi bilan' if confirmed else '⚠️ Tasdiq kodisiz (kompyuter ishlamaydi deb)'}",
    )
