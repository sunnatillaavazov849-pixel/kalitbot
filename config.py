"""Sozlamalar: hammasi .env faylidan o'qiladi."""
import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise SystemExit(f"{name} .env faylida ko'rsatilmagan")
    return value.strip()


BOT_TOKEN = _env("BOT_TOKEN")
# Tez-Tez plaginining maxfiy kaliti (TezTezAdmin.bas dagi LIC_SECRET).
# Eski TZ- parollar va yangi tizimdagi "TT" plagini shu kalit bilan hisoblanadi.
LIC_SECRET = _env("LIC_SECRET")
ADMIN_IDS = {int(x) for x in _env("ADMIN_IDS").replace(" ", "").split(",") if x}
PRICE = _env("PRICE", "100 000 so'm")          # Tez-Tez uchun boshlang'ich narx
CARD_NUMBER = _env("CARD_NUMBER", "8600 0000 0000 0000")
CARD_OWNER = _env("CARD_OWNER", "-")
DB_PATH = _env("DB_PATH", "teztez.db")

BRAND = "Sunat.cc Plaginlar"
APP_NAME = "Sunat.cc Plaginlar"    # mini ilova nomi
CONTACTS = (
    "📞 <b>Aloqa</b>\n"
    "Telegram: @sunat_aa\n"
    "Instagram: @sunat_cc\n"
    "Tel: +998 33 400 00 43"
)
