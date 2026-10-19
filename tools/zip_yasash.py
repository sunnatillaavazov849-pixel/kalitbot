"""Mijozga beriladigan plagin ZIP'ini yasaydi (botga /plagin_qosh yoki /plagin_zip bilan yuklanadi).

ZIP ichida:
  Sunat.cc Plaginlar.exe      - mini ilova
  plagin/manifest.json        - plagin haqida ma'lumot (mini ilova o'qiydi)
  plagin/<plagin>.gms         - plagin fayli(lari)
  O'qing.txt                  - qisqa yo'riqnoma

Misol:
  python tools/zip_yasash.py --prefix TT --name "Tez-Tez" --version 2.0 ^
      --gms "C:\\Plaginlar\\TezTez.gms" --exe "Sunat.cc Plaginlar.exe" --bot https://t.me/teztez_sunat_bot
"""
import argparse
import json
import os
import re
import sys
import zipfile

APP_EXE = "Sunat.cc Plaginlar.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXE = [
    os.path.join(os.getcwd(), APP_EXE),
    os.path.join(HERE, "..", "miniilova", "SunatPlaginlar", "bin", "Release", "net48", "SunatPlaginlar.exe"),
]

README = """{name} — Sunat.cc plagini

1) Shu ZIP'ni chiqarib oling (o'ng tugma -> Extract All / Извлечь все).
2) "{exe}" ni oching.
   Ko'k "Windows protected your PC" oynasi chiqsa: More info -> Run anyway.
3) "Plagin qo'shish" bo'limi plaginni o'zi taklif qiladi -> CorelDRAW versiyasini belgilang -> O'rnatish.
   (CorelDRAW yopiq bo'lsin.)
4) "Plaginlarim" -> so'rov ID'ni ({prefix}-XXXX-XXXX) nusxalab, Telegram botga yuboring.
5) To'lovdan keyin bot bergan kodni dasturga kiriting -> Faollashtirish.

Aloqa: Telegram @sunat_aa | Instagram @sunat_cc | +998 33 400 00 43
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sunat.cc plagin ZIP'ini yasash")
    ap.add_argument("--prefix", required=True, help="plagin belgisi (botdagi bilan bir xil), masalan TT")
    ap.add_argument("--name", required=True, help="plagin nomi, masalan Tez-Tez")
    ap.add_argument("--gms", required=True, nargs="+", help=".gms fayl(lar)")
    ap.add_argument("--version", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--bot", default="", help="Telegram bot havolasi, masalan https://t.me/teztez_sunat_bot")
    ap.add_argument("--exe", default="", help=f"mini ilova ({APP_EXE})")
    ap.add_argument("--out", default="", help="natija ZIP (standart: <PREFIKS>_<nom>.zip)")
    a = ap.parse_args(argv)

    prefix = a.prefix.strip().upper()
    if not re.fullmatch(r"[A-Z]{2,4}", prefix):
        sys.exit("Prefiks 2-4 ta lotin harfi bo'lishi kerak (masalan TT)")
    for g in a.gms:
        if not os.path.isfile(g):
            sys.exit(f"Fayl topilmadi: {g}")
    exe = a.exe or next((p for p in DEFAULT_EXE if os.path.isfile(p)), "")
    if not os.path.isfile(exe):
        sys.exit(f"Mini ilova topilmadi. --exe bilan ko'rsating ({APP_EXE})")

    manifest = {
        "prefix": prefix,
        "name": a.name,
        "version": a.version,
        "description": a.description,
        "bot": a.bot,
        "files": [os.path.basename(g) for g in a.gms],
    }
    safe = re.sub(r"[^A-Za-z0-9_-]+", "", a.name.replace(" ", "_")) or "plagin"
    out = a.out or f"{prefix}_{safe}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(exe, APP_EXE)
        z.writestr("plagin/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for g in a.gms:
            z.write(g, "plagin/" + os.path.basename(g))
        z.writestr("O'qing.txt", README.format(name=a.name, exe=APP_EXE, prefix=prefix).replace("\n", "\r\n"))
    print("tayyor:", os.path.abspath(out))
    return out


if __name__ == "__main__":
    main()
