"""Plagin ZIP'ini joyida yasash: plagin/<fayl>.gms + plagin/manifest.json + O'qing.txt.
Windows dastur (PackageInstaller) shu tuzilishni o'qiydi."""
import io
import json
import re
import zipfile

from django.conf import settings

README = """{name} - Sunat.cc plagini

ENG OSON YO'L
  "Sunat.cc Plaginlar" dasturini oching -> Plaginlar -> {name} -> "Plaginni o'rnatish"
  -> shu ZIP faylni tanlang. Dastur plaginni CorelDRAW'ga o'zi qo'yadi.

QO'LDA
  1) CorelDRAW'ni yoping.
  2) "plagin" papkasidagi {file} ni CorelDRAW'ning GMS papkasiga nusxalang, masalan:
       %APPDATA%\\Corel\\CorelDRAW Graphics Suite 2020\\Draw\\GMS
  3) CorelDRAW'ni oching va plaginni ishga tushiring. So'rov kodi so'ralsa - saytdan
     olgan faollashtirish kodingizni kiriting.

Yordam: {site}/yordam/
"""


def gms_filename(plugin) -> str:
    """Doimiy fayl nomi (masalan TezTez.gms). Saqlangan fayl nomiga bog'liq emas: admin yangi versiya
    yuklaganda Django nomga qo'shimcha qo'shadi, mijoz papkasida esa eski nusxa almashtirilishi kerak."""
    return (re.sub(r"[^A-Za-z0-9]+", "", plugin.name) or plugin.prefix) + ".gms"


def build_plugin_zip(plugin) -> tuple[bytes, str]:
    fname = gms_filename(plugin)
    manifest = {
        "prefix": plugin.prefix,
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.tagline,
        "bot": settings.SITE_URL,
        "files": [fname],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        with plugin.gms_file.open("rb") as f:
            z.writestr("plagin/" + fname, f.read())
        z.writestr("plagin/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("O'qing.txt", README.format(name=plugin.name, file=fname, site=settings.SITE_URL)
                   .replace("\n", "\r\n"))
    return buf.getvalue(), f"{plugin.prefix}_{plugin.slug}.zip"
