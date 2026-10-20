"""Kompyuterda sinab ko'rish uchun namuna ma'lumot (faqat DEBUG=1 da).

    python manage.py demo_malumot

Admin: login "admin", parol "admin12345" - faqat o'z kompyuteringizda sinash uchun.
Qayta ishga tushirilsa nusxa ko'paytirmaydi.
"""
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from shop.models import Plugin

PLUGINS = [
    ("TT", "Tez-Tez", "tez-tez", 150000, "2.0",
     "Obyektlarni listga zich joylashtiradi: ko'p listli taxlash, burish, rang bo'yicha ajratish.",
     "Tanlangan obyektlarni list(lar)ga zich joylashtiradi.\nMaxRects algoritmi, 90° burish, bir nechta list."),
    ("MB", "Manga Bitmap", "manga-bitmap", 90000, "1.0",
     "Rasmlarni RGB/CMYK bitmapga aylantiradi: DPI, ochroq/to'qroq, bittalab yoki birga.", ""),
]


class Command(BaseCommand):
    help = "Sinov uchun namuna ma'lumot: admin, plaginlar (faqat DEBUG=1)"

    def handle(self, **opts):
        if not settings.DEBUG:
            raise CommandError("Bu buyruq faqat sinov rejimida (DEBUG=1) ishlaydi.")
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", password="admin12345", name="Admin")
            self.stdout.write("  admin yaratildi: login admin, parol admin12345")
        for prefix, name, slug, price, version, tagline, desc in PLUGINS:
            if Plugin.objects.filter(prefix=prefix).exists():
                continue
            p = Plugin.objects.create(prefix=prefix, name=name, slug=slug, price=price, version=version,
                                      tagline=tagline, description=desc)
            p.gms_file.save(f"{name.replace(' ', '').replace('-', '')}.gms",
                            ContentFile(b"namuna - haqiqiy plagin fayli emas"))
            self.stdout.write(f"  plagin qo'shildi: {name}")
        self.stdout.write(self.style.SUCCESS("Namuna ma'lumot tayyor."))
