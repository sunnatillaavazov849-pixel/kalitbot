"""Mijozga beriladigan plagin ZIP'ini yasaydi (botga /plagin_qosh yoki /plagin_zip bilan yuklanadi).

ZIP ichida:
  O'qing.txt                  - o'rnatish yo'riqnomasi
  plagin/<plagin>.gms         - plagin fayli(lari)
  plagin/manifest.json        - plagin haqida ma'lumot (mini ilova o'qiydi)
  Sunat.cc Plaginlar.exe      - mini ilova (ixtiyoriy, faqat --exe berilsa)

Misol:
  python tools/zip_yasash.py --prefix TT --name "Tez-Tez" --version 2.0 ^
      --gms "C:\\Plaginlar\\TezTez.gms" --bot https://t.me/teztez_sunat_bot
"""
import argparse
import json
import os
import re
import sys
import zipfile

APP_EXE = "Sunat.cc Plaginlar.exe"

README = """{name} - Sunat.cc plagini

O'RNATISH
1) Shu ZIP'ni chiqarib oling (o'ng tugma -> Extract All / Извлечь все).
2) CorelDRAW'ni yoping.
3) "plagin" papkasidagi {files} faylni CorelDRAW'ning GMS papkasiga nusxalang.
   Explorer'ning manzil qatoriga yozing va Enter bosing (CorelDRAW 2020 misolida):
      %APPDATA%\\Corel\\CorelDRAW Graphics Suite 2020\\Draw\\GMS
   Boshqa versiyada "2020" o'rniga o'z versiyangiz papkasi bo'ladi.
   Bu papka bo'lmasa:  C:\\Program Files\\Corel\\<CorelDRAW papkasi>\\Draw\\GMS
4) CorelDRAW'ni oching va plaginni ishga tushiring.

FAOLLASHTIRISH
5) Plagin oynasida so'rov ID chiqadi (masalan {prefix}-K7QM-3XPA).
   U belgilangan holda turadi - Ctrl+C bilan nusxalab, Telegram botga yuboring.
6) To'lov chekini botga yuboring. Admin tasdiqlagach bot kod beradi.
7) Kodni o'sha oynaga qo'ying va OK bosing - plagin ishlaydi.

BOSHQA KOMPYUTERGA O'TISH
   CorelDRAW'da Alt+F8 -> SunatDezaktiv -> chiqqan tasdiq kodini botdagi
   "Boshqa PC'ga ko'chirish" bo'limiga yuboring. Kuniga 1, jami 3 marta.
{exe_note}
Videolar: botdagi "O'rnatish" bo'limi.
Aloqa: Telegram @sunat_aa | Instagram @sunat_cc | +998 33 400 00 43
"""

EXE_NOTE = """
OSONROQ YO'L (ixtiyoriy)
   "{exe}" ni oching (ko'k oyna chiqsa: More info -> Run anyway) ->
   "Plagin qo'shish" -> plaginni o'zi to'g'ri papkaga qo'yadi.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sunat.cc plagin ZIP'ini yasash")
    ap.add_argument("--prefix", required=True, help="plagin belgisi (botdagi bilan bir xil), masalan TT")
    ap.add_argument("--name", required=True, help="plagin nomi, masalan Tez-Tez")
    ap.add_argument("--gms", required=True, nargs="+", help=".gms fayl(lar)")
    ap.add_argument("--version", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--bot", default="", help="Telegram bot havolasi, masalan https://t.me/teztez_sunat_bot")
    ap.add_argument("--exe", default="", help=f"mini ilova ({APP_EXE}) - ixtiyoriy")
    ap.add_argument("--out", default="", help="natija ZIP (standart: <PREFIKS>_<nom>.zip)")
    a = ap.parse_args(argv)

    prefix = a.prefix.strip().upper()
    if not re.fullmatch(r"[A-Z]{2,4}", prefix):
        sys.exit("Prefiks 2-4 ta lotin harfi bo'lishi kerak (masalan TT)")
    for g in a.gms:
        if not os.path.isfile(g):
            sys.exit(f"Fayl topilmadi: {g}")
    if a.exe and not os.path.isfile(a.exe):
        sys.exit(f"Mini ilova topilmadi: {a.exe}")

    files = [os.path.basename(g) for g in a.gms]
    manifest = {
        "prefix": prefix,
        "name": a.name,
        "version": a.version,
        "description": a.description,
        "bot": a.bot,
        "files": files,
    }
    readme = README.format(
        name=a.name, prefix=prefix, files=", ".join(files),
        exe_note=EXE_NOTE.format(exe=APP_EXE) if a.exe else "",
    )
    safe = re.sub(r"[^A-Za-z0-9_-]+", "", a.name.replace(" ", "_")) or "plagin"
    out = a.out or f"{prefix}_{safe}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("O'qing.txt", readme.replace("\n", "\r\n"))
        for g in a.gms:
            z.write(g, "plagin/" + os.path.basename(g))
        z.writestr("plagin/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if a.exe:
            z.write(a.exe, APP_EXE)
    print("tayyor:", os.path.abspath(out))
    return out


if __name__ == "__main__":
    main()
