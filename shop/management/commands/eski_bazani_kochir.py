"""Eski Telegram bot bazasini (teztez.db) saytga ko'chiradi.

    python manage.py eski_bazani_kochir /yo'l/teztez.db

- Plaginlar: belgi, nom, narx, tavsif va MAXFIY KALIT (kodlar shu kalitga bog'liq).
- Mijozlar -> "Eski mijozlar": saytda shu telefon bilan ro'yxatdan o'tganda litsenziyalari o'zi ulanadi.
- Litsenziyalar holati, kompyuter ID, kod, ko'chirishlar soni bilan.
- Eski TZ- parol xaridlari -> kabinetdagi "Eski litsenziyani o'tkazish" orqali olinadi.
Qayta ishga tushirilsa dublikat qilmaydi.
"""
import re
import sqlite3
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from accounts.phone import normalize_phone
from shop import services as S
from shop.models import Deactivation, LegacyCustomer, LegacyTzOrder, License, Plugin

STATUS = {"faol": License.FAOL, "bosh": License.BOSH, "bloklangan": License.BLOKLANGAN}
SOURCE = {"xarid": License.XARID, "eski": License.ESKI, "admin": License.ADMIN}


def parse_dt(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return timezone.make_aware(datetime.strptime(value, fmt))
        except ValueError:
            pass
    return None


def parse_price(text) -> int:
    digits = re.sub(r"\D", "", str(text or ""))
    return int(digits) if digits else 0


class Command(BaseCommand):
    help = "Eski Telegram bot bazasini (teztez.db) saytga ko'chiradi"

    def add_arguments(self, parser):
        parser.add_argument("path", help="teztez.db fayli")

    def handle(self, path, **opts):
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        except sqlite3.Error as e:
            raise CommandError(f"Bazani ochib bo'lmadi: {e}")
        con.row_factory = sqlite3.Row
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "orders" not in tables:
            raise CommandError("Bu bot bazasi emas (orders jadvali yo'q).")
        cols = {r["name"] for r in con.execute("PRAGMA table_info(orders)")}
        self.report = {}
        with transaction.atomic():
            plugins = self.import_plugins(con, tables)
            customers = self.import_customers(con, tables)
            if "licenses" in tables:
                self.import_licenses(con, plugins, customers)
            self.import_tz_orders(con, cols)
            pending = con.execute("SELECT COUNT(*) FROM orders WHERE status = 'kutilmoqda'").fetchone()[0]
            linked = sum(S.claim_legacy(u) for u in User.objects.filter(
                phone__in=LegacyCustomer.objects.filter(claimed_by__isnull=True).values("phone")))
        con.close()

        for k, v in self.report.items():
            self.stdout.write(f"  {k}: {v}")
        self.stdout.write(f"  saytdagi akkauntlarga darhol ulangan litsenziyalar: {linked}")
        if pending:
            self.stdout.write(self.style.WARNING(
                f"  Botda {pending} ta tekshirilmagan to'lov bor - ular ko'chirilmaydi, botda yoki qo'lda hal qiling."))
        self.stdout.write(self.style.SUCCESS("Tayyor."))

    def bump(self, key, n=1):
        self.report[key] = self.report.get(key, 0) + n

    # ------------------------------------------------------------ plaginlar
    def import_plugins(self, con, tables) -> dict:
        result = {}
        rows = list(con.execute("SELECT * FROM plugins")) if "plugins" in tables else []
        if not rows and settings.LIC_SECRET:
            # eng eski bot: plugins jadvali yo'q, faqat Tez-Tez
            rows = [{"prefix": "TT", "name": "Tez-Tez", "description": "", "price": "0",
                     "secret": settings.LIC_SECRET, "active": 1}]
        for r in rows:
            prefix = r["prefix"].upper()
            plugin = Plugin.objects.filter(prefix=prefix).first()
            if plugin is None:
                slug = slugify(r["name"]) or prefix.lower()
                if Plugin.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{prefix.lower()}"
                plugin = Plugin.objects.create(prefix=prefix, name=r["name"], slug=slug,
                                               description=r["description"] or "", price=parse_price(r["price"]),
                                               secret=r["secret"], active=bool(r["active"]))
                self.bump("yangi plaginlar")
            elif plugin.secret != r["secret"]:
                if plugin.licenses.exclude(legacy_id__isnull=False).exists():
                    raise CommandError(
                        f"{prefix} plaginining saytdagi kaliti botdagidan farq qiladi va saytda allaqachon "
                        f"litsenziyalar bor. Kalitlarni qo'lda solishtiring.")
                plugin.secret = r["secret"]
                plugin.save(update_fields=["secret"])
                self.bump("kaliti botdagiga moslangan plaginlar")
            if prefix == "TT" and settings.LIC_SECRET and plugin.secret != settings.LIC_SECRET:
                self.stdout.write(self.style.WARNING(
                    "  Diqqat: Tez-Tez kaliti .env dagi LIC_SECRET bilan bir xil emas."))
            result[prefix] = plugin
        return result

    # ------------------------------------------------------------ mijozlar
    def import_customers(self, con, tables) -> dict:
        people = {}
        if "users" in tables:
            for r in con.execute("SELECT user_id, name, phone FROM users"):
                people[r["user_id"]] = (r["name"], r["phone"])
        for r in con.execute("SELECT user_id, name, phone FROM orders ORDER BY id"):
            people.setdefault(r["user_id"], (r["name"], r["phone"]))
        result = {}
        for tg_id, (name, phone) in people.items():
            phone = normalize_phone(phone) or (phone or "")[:16]
            lc, created = LegacyCustomer.objects.get_or_create(
                telegram_id=tg_id, defaults={"name": (name or "")[:80], "phone": phone})
            if created:
                self.bump("eski mijozlar")
            result[tg_id] = lc
        return result

    # ------------------------------------------------------------ litsenziyalar
    def import_licenses(self, con, plugins, customers):
        for r in con.execute("SELECT * FROM licenses ORDER BY id"):
            if License.objects.filter(legacy_id=r["id"]).exists():
                continue
            plugin = plugins.get(r["plugin"])
            owner = customers.get(r["user_id"])
            if plugin is None or owner is None:
                self.bump("o'tkazib yuborilgan litsenziyalar (plagin yoki mijoz topilmadi)")
                continue
            status = STATUS.get(r["status"], License.BOSH)
            lic = License.objects.create(
                legacy_owner=owner, plugin=plugin, legacy_id=r["id"],
                mid=(r["mid"] or "") if status == License.FAOL else "",
                code=(r["code"] or "") if status == License.FAOL else "",
                status=status, source=SOURCE.get(r["source"], License.XARID),
                deact_count=r["deact_count"] or 0, last_deact_at=parse_dt(r["last_deact_at"]),
                activated_at=parse_dt(r["activated_at"]),
            )
            License.objects.filter(pk=lic.pk).update(created_at=parse_dt(r["created_at"]) or timezone.now())
            self.bump("litsenziyalar")
        try:
            rows = list(con.execute("SELECT * FROM deactivations ORDER BY id"))
        except sqlite3.Error:
            rows = []
        for r in rows:
            lic = License.objects.filter(legacy_id=r["license_id"]).first()
            if lic is None or lic.deactivations.filter(reason=r["reason"], mid=r["mid"] or "").exists():
                continue
            d = Deactivation.objects.create(license=lic, mid=r["mid"] or "", reason=r["reason"],
                                            confirmed=bool(r["confirmed"]))
            Deactivation.objects.filter(pk=d.pk).update(created_at=parse_dt(r["created_at"]) or timezone.now())
            self.bump("kompyuter almashtirishlar tarixi")

    # ------------------------------------------------------------ eski TZ- parollar
    def import_tz_orders(self, con, cols):
        where = "status = 'tasdiqlandi'" + (" AND plugin IS NULL" if "plugin" in cols else "")
        for r in con.execute(f"SELECT * FROM orders WHERE {where} ORDER BY id"):
            if LegacyTzOrder.objects.filter(legacy_id=r["id"]).exists():
                continue
            # bot ichida allaqachon yangi tizimga o'tkazilganmi (source='eski', order_id=shu buyurtma)
            migrated = License.objects.filter(legacy_id__in=[
                x[0] for x in con.execute("SELECT id FROM licenses WHERE source='eski' AND order_id=?", (r["id"],))
            ]).first() if self._has_licenses(con) else None
            LegacyTzOrder.objects.create(
                legacy_id=r["id"], machine_code=r["machine_code"], name=(r["name"] or "")[:80],
                phone=(r["phone"] or "")[:32], telegram_id=r["user_id"], password=r["password"] or "",
                created_at=(r["created_at"] or "")[:20], license=migrated)
            self.bump("eski TZ- xaridlar")

    def _has_licenses(self, con):
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='licenses'").fetchone() is not None
