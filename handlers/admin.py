"""Admin buyruqlari: plaginlar, videolar, litsenziyalar, buyurtmalar."""
import html

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
import db as dbm
from litsenziya import activation_code, is_valid_prefix, make_password, normalize_machine_code, parse_request_id
from .common import db, esc, is_admin, plugin_name, user_label
from .keyboards import MAIN_KB

router = Router()
# barcha buyruqlar faqat adminlar uchun; boshqalarga bu router umuman ishlamaydi
router.message.filter(lambda m: m.from_user and is_admin(m.from_user.id))
router.callback_query.filter(lambda c: is_admin(c.from_user.id))


class AddPlugin(StatesGroup):
    prefix = State()
    name = State()
    price = State()
    description = State()
    zip = State()


class Upload(StatesGroup):
    plugin_zip = State()
    video = State()
    video_title = State()


HELP = (
    "🛠 <b>Admin buyruqlari</b>\n\n"
    "<b>Plaginlar</b>\n"
    "/plaginlar — ro'yxat\n"
    "/plagin_qosh — yangi plagin (bosqichma-bosqich)\n"
    "/plagin_zip TT — ZIP faylni almashtirish\n"
    "/plagin_narx TT 150 000 so'm\n"
    "/plagin_tavsif TT matn\n"
    "/plagin_yoq TT — sotuvni yoqish/o'chirish\n"
    "/plagin_kalit TT — maxfiy kalit (plaginga yoziladi)\n\n"
    "<b>Videolar</b>\n"
    "/video_qosh — o'rnatish videosi qo'shish\n"
    "/videolar — ro'yxat va o'chirish\n\n"
    "<b>Litsenziyalar</b>\n"
    "/litsenziyalar [TT] — oxirgi 30 ta\n"
    "/bloklangan — bloklanganlar\n"
    "/blokdan_chiqar 12 — blokdan chiqarish (ko'chirishlar 0 ga tushadi)\n"
    "/litsenziya_ber USER_ID TT — to'lovsiz litsenziya berish\n"
    "/kod TT-K7QM-3XPA — kodni hisoblab ko'rish\n\n"
    "<b>Buyurtmalar</b>\n"
    "/royxat — oxirgi 30 ta buyurtma\n"
    "/parol K7QM-3XPA — eski TZ- parol\n\n"
    "Bekor qilish: /bekor"
)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(HELP)


# ---------------------------------------------------------------- plaginlar

@router.message(Command("plaginlar"))
async def cmd_plugins(message: Message):
    plugins = db.plugins(only_active=False)
    if not plugins:
        await message.answer("Plaginlar yo'q. /plagin_qosh")
        return
    counts = db.license_counts()
    lines = ["🧩 <b>Plaginlar</b>"]
    for p in plugins:
        c = counts.get(p["prefix"], {})
        lines.append(
            f"\n<b>{p['prefix']}</b> — {esc(p['name'])} {'🟢' if p['active'] else '🔴 sotuvda emas'}\n"
            f"💰 {esc(p['price'])} · 📦 ZIP: {'bor' if p['zip_file_id'] else '❌ yo‘q'}\n"
            f"🔑 faol {c.get(dbm.FAOL, 0)} · bo'sh {c.get(dbm.BOSH, 0)} · blok {c.get(dbm.BLOKLANGAN, 0)}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("plagin_qosh"))
async def cmd_add_plugin(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddPlugin.prefix)
    await message.answer(
        "Yangi plagin.\n1/5. <b>Belgi (prefiks)</b> — 2–4 ta lotin harfi, masalan <code>MB</code>.\n"
        "U so'rov ID va kodlar boshida turadi va keyin o'zgartirilmaydi."
    )


@router.message(AddPlugin.prefix, F.text)
async def ap_prefix(message: Message, state: FSMContext):
    prefix = message.text.strip().upper()
    if not is_valid_prefix(prefix):
        await message.answer("2–4 ta lotin harfi bo'lishi kerak (masalan MB):")
        return
    if db.get_plugin(prefix):
        await message.answer("Bu belgi band. Boshqasini yozing:")
        return
    await state.update_data(prefix=prefix)
    await state.set_state(AddPlugin.name)
    await message.answer("2/5. Plagin <b>nomi</b> (masalan: Manga Bitmap):")


@router.message(AddPlugin.name, F.text)
async def ap_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()[:64])
    await state.set_state(AddPlugin.price)
    await message.answer("3/5. <b>Narxi</b> (masalan: 150 000 so'm):")


@router.message(AddPlugin.price, F.text)
async def ap_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text.strip()[:64])
    await state.set_state(AddPlugin.description)
    await message.answer("4/5. Qisqa <b>tavsif</b> (yoki <code>-</code>):")


@router.message(AddPlugin.description, F.text)
async def ap_desc(message: Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description="" if desc == "-" else desc[:1000])
    await state.set_state(AddPlugin.zip)
    await message.answer("5/5. Mijozga beriladigan <b>ZIP faylni</b> yuboring (yoki /otkazish — keyin /plagin_zip bilan).")


@router.message(AddPlugin.zip, Command("otkazish"))
@router.message(AddPlugin.zip, F.document)
async def ap_zip(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    secret = db.add_plugin(data["prefix"], data["name"], data["price"], data["description"])
    if message.document:
        db.update_plugin(data["prefix"], zip_file_id=message.document.file_id, zip_name=message.document.file_name)
    await message.answer(
        f"✅ Plagin qo'shildi: <b>{data['prefix']}</b> — {esc(data['name'])}\n\n"
        f"🔐 Maxfiy kalit:\n<code>{secret}</code>\n\n"
        "Bu kalitni plaginning <code>SunatLicense.bas</code> moduliga (<code>LIC_SECRET</code>) yozasiz. "
        "Hech kimga bermang. Keyin ham ko'rish mumkin: "
        f"<code>/plagin_kalit {data['prefix']}</code>\n\n"
        "⚠️ Bot bazasi (teztez.db) yo'qolsa, kalitlar ham yo'qoladi — bazaning nusxasini saqlab turing."
    )


@router.message(Command("plagin_zip"))
async def cmd_plugin_zip(message: Message, state: FSMContext, command: CommandObject):
    prefix = (command.args or "").strip().upper()
    if not db.get_plugin(prefix):
        await message.answer("Foydalanish: <code>/plagin_zip TT</code>")
        return
    await state.clear()
    await state.update_data(prefix=prefix)
    await state.set_state(Upload.plugin_zip)
    await message.answer(f"<b>{prefix}</b> uchun yangi ZIP faylni yuboring:")


@router.message(Upload.plugin_zip, F.document)
async def got_plugin_zip(message: Message, state: FSMContext):
    prefix = (await state.get_data())["prefix"]
    await state.clear()
    db.update_plugin(prefix, zip_file_id=message.document.file_id, zip_name=message.document.file_name)
    await message.answer(f"✅ {prefix} ZIP fayli yangilandi: {esc(message.document.file_name or '')}")


def _prefix_and_rest(command: CommandObject):
    parts = (command.args or "").split(maxsplit=1)
    prefix = parts[0].upper() if parts else ""
    return prefix, (parts[1].strip() if len(parts) > 1 else "")


@router.message(Command("plagin_narx"))
async def cmd_price(message: Message, command: CommandObject):
    prefix, rest = _prefix_and_rest(command)
    if not rest or not db.update_plugin(prefix, price=rest[:64]):
        await message.answer("Foydalanish: <code>/plagin_narx TT 150 000 so'm</code>")
        return
    await message.answer(f"✅ {prefix} narxi: {esc(rest)}")


@router.message(Command("plagin_tavsif"))
async def cmd_desc(message: Message, command: CommandObject):
    prefix, rest = _prefix_and_rest(command)
    if not rest or not db.update_plugin(prefix, description=rest[:1000]):
        await message.answer("Foydalanish: <code>/plagin_tavsif TT matn</code>")
        return
    await message.answer(f"✅ {prefix} tavsifi yangilandi.")


@router.message(Command("plagin_yoq"))
async def cmd_toggle(message: Message, command: CommandObject):
    prefix, _ = _prefix_and_rest(command)
    p = db.get_plugin(prefix)
    if p is None:
        await message.answer("Foydalanish: <code>/plagin_yoq TT</code>")
        return
    db.update_plugin(prefix, active=0 if p["active"] else 1)
    await message.answer(f"{prefix}: {'🔴 sotuvdan olindi' if p['active'] else '🟢 sotuvga qo‘yildi'}")


@router.message(Command("plagin_kalit"))
async def cmd_secret(message: Message, command: CommandObject):
    prefix, _ = _prefix_and_rest(command)
    p = db.get_plugin(prefix)
    if p is None:
        await message.answer("Foydalanish: <code>/plagin_kalit TT</code>")
        return
    await message.answer(f"🔐 {prefix} maxfiy kaliti:\n<code>{esc(p['secret'])}</code>\nHech kimga bermang.")


# ---------------------------------------------------------------- videolar

@router.message(Command("video_qosh"))
async def cmd_add_video(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Upload.video)
    await message.answer("Videoni yuboring. Izoh (caption) qismiga sarlavha yozsangiz, u nom bo'ladi.")


@router.message(Upload.video, F.video)
async def got_video(message: Message, state: FSMContext):
    if message.caption:
        await state.clear()
        vid = db.add_video(message.caption.strip()[:100], message.video.file_id)
        await message.answer(f"✅ Video #{vid} qo'shildi: {esc(message.caption.strip())}")
        return
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(Upload.video_title)
    await message.answer("Video sarlavhasini yozing (masalan: Mini ilovani o'rnatish):")


@router.message(Upload.video_title, F.text)
async def got_video_title(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    vid = db.add_video(message.text.strip()[:100], data["file_id"])
    await message.answer(f"✅ Video #{vid} qo'shildi.")


@router.message(Command("videolar"))
async def cmd_videos(message: Message):
    vids = db.videos()
    if not vids:
        await message.answer("Videolar yo'q. /video_qosh")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 #{v['id']} {v['title']}", callback_data=f"vdel:{v['id']}")] for v in vids
    ])
    await message.answer("🎬 Videolar (o'chirish uchun bosing):", reply_markup=kb)


@router.callback_query(F.data.regexp(r"^vdel:\d+$"))
async def cb_vdel(call: CallbackQuery):
    vid = int(call.data[5:])
    db.delete_video(vid)
    await call.answer(f"Video #{vid} o'chirildi")
    vids = db.videos()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 #{v['id']} {v['title']}", callback_data=f"vdel:{v['id']}")] for v in vids
    ]) if vids else None
    await call.message.edit_text("🎬 Videolar (o'chirish uchun bosing):" if vids else "Videolar yo'q.", reply_markup=kb)


# ---------------------------------------------------------------- litsenziyalar

STATUS_ICON = {dbm.FAOL: "🟢", dbm.BOSH: "⚪️", dbm.BLOKLANGAN: "⛔"}


async def send_long(message: Message, header: str, items: list[str]):
    chunks = [header]
    for item in items:
        if len(chunks[-1]) + len(item) > 3800:
            chunks.append("")
        chunks[-1] += item
    for chunk in chunks:
        await message.answer(chunk)


def license_line(l) -> str:
    who = f"{esc(l['uname'])}, {esc(l['uphone'])}" if l["uname"] else f"ID {l['user_id']}"
    mid = f" · <code>{l['mid']}</code>" if l["mid"] else ""
    return (
        f"\n{STATUS_ICON.get(l['status'], '•')} #{l['id']} <b>{l['plugin']}</b>{mid} · "
        f"🔄 {l['deact_count']}/{dbm.MAX_DEACT} · {l['source']}\n   {who} (ID <code>{l['user_id']}</code>)\n"
    )


@router.message(Command("litsenziyalar"))
async def cmd_licenses(message: Message, command: CommandObject):
    prefix = (command.args or "").strip().upper() or None
    rows = db.licenses(plugin=prefix)
    if not rows:
        await message.answer("Litsenziyalar yo'q.")
        return
    await send_long(message, f"🔑 <b>Oxirgi {len(rows)} ta litsenziya</b>\n", [license_line(l) for l in rows])


@router.message(Command("bloklangan"))
async def cmd_blocked(message: Message):
    rows = db.licenses(status=dbm.BLOKLANGAN, limit=100)
    if not rows:
        await message.answer("Bloklangan litsenziya yo'q.")
        return
    await send_long(message, "⛔ <b>Bloklangan</b> (chiqarish: /blokdan_chiqar ID)\n", [license_line(l) for l in rows])


@router.message(Command("blokdan_chiqar"))
async def cmd_unblock(message: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if not arg.isdigit() or not db.unblock(int(arg)):
        await message.answer("Foydalanish: <code>/blokdan_chiqar 12</code> (faqat bloklangan litsenziya uchun)")
        return
    lic = db.get_license(int(arg))
    await message.answer(f"✅ Litsenziya #{arg} blokdan chiqarildi, ko'chirishlar soni 0 ga tushdi.")
    try:
        await message.bot.send_message(
            lic["user_id"],
            f"✅ <b>{esc(plugin_name(lic['plugin']))}</b> litsenziyangiz blokdan chiqarildi.\n"
            f"Yangi kompyuterda {config.APP_NAME} dasturidagi so'rov ID'ni yuboring — kod to'lovsiz beriladi.",
            reply_markup=MAIN_KB,
        )
    except Exception:
        pass


@router.message(Command("litsenziya_ber"))
async def cmd_grant(message: Message, command: CommandObject):
    parts = (command.args or "").split()
    if len(parts) != 2 or not parts[0].isdigit() or not db.get_plugin(parts[1].upper()):
        await message.answer(
            "Foydalanish: <code>/litsenziya_ber USER_ID TT</code>\n"
            "USER_ID — mijozning Telegram ID raqami (mijoz botga /start bosgan bo'lishi kerak)."
        )
        return
    uid, prefix = int(parts[0]), parts[1].upper()
    lic_id = db.create_license(uid, prefix, dbm.ADMIN)
    await message.answer(f"✅ Litsenziya #{lic_id} ({prefix}) berildi → {user_label(uid)}")
    try:
        await message.bot.send_message(
            uid,
            f"🎁 Sizga <b>{esc(plugin_name(prefix))}</b> litsenziyasi berildi.\n"
            f"{config.APP_NAME} dasturidagi so'rov ID'ni shu yerga yuboring — kod to'lovsiz beriladi.",
            reply_markup=MAIN_KB,
        )
    except Exception:
        await message.answer("⚠️ Mijozga xabar yuborib bo'lmadi (u botga /start bosmagan bo'lishi mumkin).")


@router.message(Command("kod"))
async def cmd_code(message: Message, command: CommandObject):
    parsed = parse_request_id(command.args or "", db.prefixes())
    if parsed is None:
        await message.answer("Foydalanish: <code>/kod TT-K7QM-3XPA</code>")
        return
    prefix, mid = parsed
    code = activation_code(prefix, mid, db.get_plugin(prefix)["secret"])
    await message.answer(f"🧩 {prefix} · 💻 <code>{mid}</code>\n🔑 <code>{code}</code>")


# ---------------------------------------------------------------- buyurtmalar

@router.message(Command("royxat"))
async def cmd_list(message: Message):
    rows = db.recent(30)
    if not rows:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return
    icons = {dbm.KUTILMOQDA: "⏳", dbm.TASDIQLANDI: "✅", dbm.RAD_ETILDI: "❌"}
    s = db.stats()
    header = (
        f"<b>Oxirgi {len(rows)} ta buyurtma</b>\n"
        f"⏳ {s.get(dbm.KUTILMOQDA, 0)}  ✅ {s.get(dbm.TASDIQLANDI, 0)}  ❌ {s.get(dbm.RAD_ETILDI, 0)}\n"
    )
    items = []
    for o in rows:
        plug = o["plugin"] or "TZ (eski)"
        items.append(
            f"\n{icons.get(o['status'], '•')} #{o['id']} {o['created_at']} · {plug}\n"
            f"   {html.escape(o['name'])}, {html.escape(o['phone'])}\n"
            f"   <code>{o['machine_code']}</code>"
            + (f" → <code>{o['password']}</code>" if o["password"] else "")
            + "\n"
        )
    await send_long(message, header, items)


@router.message(Command("parol"))
async def cmd_password(message: Message, command: CommandObject):
    code = normalize_machine_code(command.args or "")
    if code is None:
        await message.answer("Foydalanish: <code>/parol K7QM-3XPA</code> (eski TZ- tizimi)")
        return
    await message.answer(f"💻 <code>{code}</code>\n🔑 <code>{make_password(code, config.LIC_SECRET)}</code>")
