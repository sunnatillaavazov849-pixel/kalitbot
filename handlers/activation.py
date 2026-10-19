"""So'rov ID -> to'lov -> admin tasdig'i -> faollashtirish kodi. Eski TZ- litsenziyani ko'chirish."""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
import db as dbm
from litsenziya import activation_code, make_password, normalize_machine_code, parse_request_id
from .common import db, esc, is_admin, notify_admins, plugin_name, user_label
from .keyboards import MAIN_KB, MENU_BUTTONS
from .start import require_user

router = Router()


class Act(StatesGroup):
    request = State()
    receipt = State()


class Leg(StatesGroup):
    code = State()


REQUEST_HELP = (
    "🔑 <b>Faollashtirish</b>\n\n"
    f"<b>{config.APP_NAME}</b> dasturini oching → <b>Plaginlarim</b> → kerakli plagin kartochkasidagi "
    "<b>so'rov ID</b>'ni nusxalang (masalan <code>TT-K7QM-3XPA</code>) va shu yerga yuboring.\n\n"
    "Bekor qilish: /bekor"
)


async def is_request_id(message: Message) -> bool:
    return bool(message.text) and parse_request_id(message.text, db.prefixes()) is not None


async def ask_request(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Act.request)
    await message.answer(REQUEST_HELP)


@router.message(Act.request, F.text)
async def got_request(message: Message, state: FSMContext):
    parsed = parse_request_id(message.text, db.prefixes())
    if parsed is None:
        await message.answer(
            "So'rov ID noto'g'ri. U plagin belgisi va 8 ta belgidan iborat, masalan "
            "<code>TT-K7QM-3XPA</code>. Dasturdan aynan ko'chirib yuboring:"
        )
        return
    await state.clear()
    await handle_request(message, state, *parsed)


# Menyu holatidan tashqari ham: so'rov ID ko'rinishidagi har qanday xabar tushuniladi
@router.message(StateFilter(None), F.text, is_request_id)
async def got_request_anytime(message: Message, state: FSMContext):
    await handle_request(message, state, *parse_request_id(message.text, db.prefixes()))


async def handle_request_text(message: Message, state: FSMContext, text: str):
    parsed = parse_request_id(text, db.prefixes())
    if parsed:
        await handle_request(message, state, *parsed)


async def send_code(bot: Bot, chat_id: int, prefix: str, mid: str, code: str, title: str):
    await bot.send_message(
        chat_id,
        f"{title}\n\n"
        f"🧩 Plagin: <b>{esc(plugin_name(prefix))}</b>\n"
        f"💻 Kompyuter ID: <code>{mid}</code>\n"
        f"🔑 Faollashtirish kodi: <code>{code}</code>\n\n"
        f"Kodni <b>{config.APP_NAME}</b> dasturida shu plagin kartochkasidagi maydonga kiriting "
        "va <b>Faollashtirish</b> tugmasini bosing.\n"
        "⚠️ Kod faqat shu kompyuterda ishlaydi.",
        reply_markup=MAIN_KB,
    )


async def handle_request(message: Message, state: FSMContext, prefix: str, mid: str):
    user = await require_user(message, state, pending=f"{prefix}-{mid}")
    if user is None:
        return
    uid = user["user_id"]
    plugin = db.get_plugin(prefix)
    if plugin is None or not plugin["active"]:
        await message.answer("Bu plagin hozir sotilmayapti. Admin bilan bog'laning: @sunat_aa")
        return

    lics = db.user_licenses(uid, prefix)
    same = next((l for l in lics if l["status"] == dbm.FAOL and l["mid"] == mid), None)
    if same:
        await send_code(message.bot, uid, prefix, mid, same["code"], "Bu kompyuter uchun kodingiz:")
        return

    free = next((l for l in lics if l["status"] == dbm.BOSH), None)
    if free:
        code = activation_code(prefix, mid, plugin["secret"])
        db.bind_license(free["id"], mid, code)
        await send_code(message.bot, uid, prefix, mid, code, "✅ Litsenziyangiz yangi kompyuterga o'tkazildi (to'lovsiz).")
        await notify_admins(
            message.bot,
            f"🔁 Litsenziya #{free['id']} yangi kompyuterga bog'landi\n"
            f"🧩 {esc(plugin['name'])} · 💻 <code>{mid}</code>\n👤 {user_label(uid)}",
        )
        return

    if db.pending_order(uid, prefix, mid):
        await message.answer("⏳ Bu so'rov bo'yicha to'lovingiz admin tomonidan tekshirilmoqda. Iltimos, kuting.")
        return

    active_other = next((l for l in lics if l["status"] == dbm.FAOL), None)
    buy_btn = InlineKeyboardButton(text="🛒 Yangi litsenziya sotib olish", callback_data=f"buy:{prefix}:{mid}")
    if active_other:
        await message.answer(
            f"Sizda <b>{esc(plugin['name'])}</b> litsenziyasi boshqa kompyuterda "
            f"(<code>{active_other['mid']}</code>) faol.\n\n"
            "Uni shu kompyuterga o'tkazish uchun avval eski kompyuterda dezaktiv qiling "
            "yoki shu kompyuter uchun yangi litsenziya sotib oling.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Eski kompyuterdan ko'chirish", callback_data=f"tr:{active_other['id']}")],
                [buy_btn],
            ]),
        )
        return

    if any(l["status"] == dbm.BLOKLANGAN for l in lics):
        await message.answer(
            f"⛔ <b>{esc(plugin['name'])}</b> litsenziyangiz bloklangan (ko'chirishlar soni oshib ketgan).\n"
            "Admin bilan bog'laning (@sunat_aa) yoki yangi litsenziya sotib oling.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[buy_btn]]),
        )
        return

    await start_purchase(message, state, prefix, mid)


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery, state: FSMContext):
    _, prefix, mid = call.data.split(":")
    await call.answer()
    await start_purchase(call.message, state, prefix, mid)


async def start_purchase(message: Message, state: FSMContext, prefix: str, mid: str):
    plugin = db.get_plugin(prefix)
    await state.clear()
    await state.update_data(plugin=prefix, mid=mid)
    await state.set_state(Act.receipt)
    await message.answer(
        f"🧩 Plagin: <b>{esc(plugin['name'])}</b>\n"
        f"💻 Kompyuter ID: <code>{mid}</code>\n\n"
        f"💰 Narx: <b>{esc(plugin['price'])}</b>\n"
        f"💳 Karta: <code>{esc(config.CARD_NUMBER)}</code>\n"
        f"👤 Karta egasi: {esc(config.CARD_OWNER)}\n\n"
        "To'lovni amalga oshirib, <b>chek rasmini</b> shu yerga yuboring.\nBekor qilish: /bekor"
    )


@router.message(Act.receipt, F.photo)
async def got_receipt_photo(message: Message, state: FSMContext):
    await submit_order(message, state, "photo:" + message.photo[-1].file_id)


@router.message(Act.receipt, F.document)
async def got_receipt_doc(message: Message, state: FSMContext):
    mime = message.document.mime_type or ""
    if not (mime.startswith("image/") or mime == "application/pdf"):
        await message.answer("Iltimos, chekni rasm (yoki PDF) ko'rinishida yuboring.")
        return
    await submit_order(message, state, "doc:" + message.document.file_id)


@router.message(Act.receipt, ~F.text.in_(MENU_BUTTONS))
async def receipt_wrong(message: Message):
    await message.answer("To'lov chekini rasm ko'rinishida yuboring. Bekor qilish: /bekor")


def order_text(o) -> str:
    if o["plugin"]:
        head = f"<b>Buyurtma #{o['id']}</b> — 🧩 {esc(plugin_name(o['plugin']))}"
        mc = f"💻 Kompyuter ID: <code>{o['machine_code']}</code>"
    else:
        kind = "🔄 QAYTA FAOLLASHTIRISH" if o["kind"] == dbm.QAYTA else "🛒 YANGI XARID"
        head = f"<b>Buyurtma #{o['id']}</b> — {kind} (eski TZ- tizimi)"
        mc = f"💻 Kompyuter kodi: <code>{o['machine_code']}</code>"
    username = f"@{o['username']}" if o["username"] else "—"
    return "\n".join([
        head,
        f"👤 Ism: {esc(o['name'])}",
        f"📱 Telefon: {esc(o['phone'])}",
        f"💬 Telegram: {esc(username)} (ID: <code>{o['user_id']}</code>)",
        mc,
        f"🕒 Sana: {o['created_at']}",
    ])


def decision_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok:{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no:{order_id}"),
    ]])


async def submit_order(message: Message, state: FSMContext, receipt: str):
    data = await state.get_data()
    await state.clear()
    user = db.get_user(message.from_user.id)
    order_id = db.add_order(
        user["user_id"], message.from_user.username, user["name"], user["phone"],
        data["mid"], dbm.YANGI, receipt, plugin=data["plugin"],
    )
    o = db.get(order_id)
    text, kb = order_text(o), decision_kb(order_id)
    for admin_id in config.ADMIN_IDS:
        try:
            if receipt.startswith("photo:"):
                await message.bot.send_photo(admin_id, receipt[6:], caption=text, reply_markup=kb)
            else:
                await message.bot.send_document(admin_id, receipt[4:], caption=text, reply_markup=kb)
        except Exception:
            logging.exception("Adminga (%s) yuborib bo'lmadi", admin_id)
    await message.answer(
        f"✅ So'rovingiz qabul qilindi (#{order_id}).\n"
        "Admin tekshirgach, faollashtirish kodi shu yerga yuboriladi. Iltimos, kuting.",
        reply_markup=MAIN_KB,
    )


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
    if o["status"] != dbm.KUTILMOQDA:
        await call.answer(f"Bu buyurtma allaqachon ko'rib chiqilgan: {o['status']}", show_alert=True)
        return

    delivered = ""
    if action == "ok":
        if o["plugin"]:
            plugin = db.get_plugin(o["plugin"])
            code = activation_code(o["plugin"], o["machine_code"], plugin["secret"])
            db.decide(order_id, dbm.TASDIQLANDI, code)
            lic_id = db.create_license(o["user_id"], o["plugin"], dbm.XARID, o["machine_code"], code, order_id)
            db.conn.execute("UPDATE orders SET license_id = ? WHERE id = ?", (lic_id, order_id))
            db.conn.commit()
            result = f"\n\n✅ <b>TASDIQLANDI</b> (litsenziya #{lic_id})\n🔑 Kod: <code>{code}</code>"
            try:
                await send_code(call.bot, o["user_id"], o["plugin"], o["machine_code"], code,
                                "✅ To'lovingiz tasdiqlandi!")
            except Exception:
                logging.exception("Foydalanuvchiga (%s) yuborib bo'lmadi", o["user_id"])
                delivered = "\n⚠️ Foydalanuvchiga yuborib bo'lmadi."
        else:
            # eski TZ- tizimidagi kutilib qolgan buyurtma
            password = make_password(o["machine_code"], config.LIC_SECRET)
            db.decide(order_id, dbm.TASDIQLANDI, password)
            result = f"\n\n✅ <b>TASDIQLANDI</b>\n🔑 Parol: <code>{password}</code>"
            try:
                await call.bot.send_message(
                    o["user_id"],
                    f"✅ To'lovingiz tasdiqlandi!\n\n💻 Kompyuter kodi: <code>{o['machine_code']}</code>\n"
                    f"🔑 Parol: <code>{password}</code>",
                    reply_markup=MAIN_KB,
                )
            except Exception:
                delivered = "\n⚠️ Foydalanuvchiga yuborib bo'lmadi."
    else:
        db.decide(order_id, dbm.RAD_ETILDI)
        result = "\n\n❌ <b>RAD ETILDI</b>"
        try:
            await call.bot.send_message(
                o["user_id"],
                f"❌ To'lov tasdiqlanmadi.\nSavollar bo'lsa, admin bilan bog'laning.\n\n{config.CONTACTS}",
                reply_markup=MAIN_KB,
            )
        except Exception:
            delivered = "\n⚠️ Foydalanuvchiga yuborib bo'lmadi."

    new_text = order_text(db.get(order_id)) + result + delivered
    try:
        if call.message.photo or call.message.document:
            await call.message.edit_caption(caption=new_text, reply_markup=None)
        else:
            await call.message.edit_text(new_text, reply_markup=None)
    except Exception:
        logging.exception("Admin xabarini yangilab bo'lmadi")
    await call.answer("Bajarildi")


# ---------------------------------------------------------------- eski TZ- litsenziya

async def ask_legacy(message: Message, state: FSMContext):
    if await require_user(message, state) is None:
        return
    await state.set_state(Leg.code)
    await message.answer(
        "♻️ <b>Eski litsenziyani ko'chirish</b>\n\n"
        "Agar Tez-Tez'ni avval <code>TZ-...</code> parol bilan sotib olgan bo'lsangiz, uni yangi tizimga "
        "bepul o'tkazamiz.\n\n"
        "Eski parolni olgan paytingizdagi <b>kompyuter kodini</b> yuboring (masalan <code>K7QM-3XPA</code>).\n"
        "Bekor qilish: /bekor"
    )


@router.message(Leg.code, F.text, ~F.text.in_(MENU_BUTTONS))
async def got_legacy(message: Message, state: FSMContext):
    mc = normalize_machine_code(message.text)
    if mc is None:
        await message.answer("Kod noto'g'ri. U 8 ta belgidan iborat, masalan <code>K7QM-3XPA</code>:")
        return
    await state.clear()
    o = db.legacy_order(mc)
    if o is None:
        await message.answer(
            "Bu kod bo'yicha tasdiqlangan xarid topilmadi.\n"
            f"Admin bilan bog'laning — u qo'lda o'tkazib beradi.\n\n{config.CONTACTS}",
            reply_markup=MAIN_KB,
        )
        return
    if db.legacy_migrated(o["id"]):
        await message.answer("Bu litsenziya allaqachon yangi tizimga o'tkazilgan. 📂 Litsenziyalarim bo'limini ko'ring.",
                             reply_markup=MAIN_KB)
        return
    uid = message.from_user.id
    lic_id = db.create_license(uid, "TT", dbm.ESKI, order_id=o["id"])
    await message.answer(
        "✅ Eski litsenziyangiz yangi tizimga o'tkazildi.\n\n"
        f"Endi <b>{config.APP_NAME}</b> dasturini o'rnating, Tez-Tez plaginini qo'shing va dastur ko'rsatgan "
        "so'rov ID'ni shu yerga yuboring — kod <b>to'lovsiz</b> beriladi.",
        reply_markup=MAIN_KB,
    )
    other = "" if o["user_id"] == uid else f"\n⚠️ Eski buyurtma boshqa akkauntdan edi (ID <code>{o['user_id']}</code>)"
    await notify_admins(
        message.bot,
        f"♻️ Eski litsenziya ko'chirildi → litsenziya #{lic_id}\n"
        f"Eski buyurtma #{o['id']}, kod <code>{mc}</code>\n👤 {user_label(uid)}{other}",
    )
