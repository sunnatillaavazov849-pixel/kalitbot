"""eski_bazani_kochir: eski Telegram bot bazasi (aynan o'sha sxema) saytga to'g'ri ko'chadimi."""
import io
import os
import sqlite3
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.models import User
from shop import licensing as L
from shop import services as S
from shop.models import Deactivation, LegacyCustomer, LegacyTzOrder, License, Plugin

# kalitbot/db.py (Telegram bot) dagi sxema
OLD_SCHEMA = """
CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, username TEXT,
  name TEXT NOT NULL, phone TEXT NOT NULL, machine_code TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'yangi',
  receipt_file_id TEXT, status TEXT NOT NULL DEFAULT 'kutilmoqda', password TEXT, created_at TEXT NOT NULL,
  decided_at TEXT, plugin TEXT, license_id INTEGER);
CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT, name TEXT NOT NULL, phone TEXT NOT NULL,
  created_at TEXT NOT NULL);
CREATE TABLE plugins (prefix TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
  price TEXT NOT NULL, zip_file_id TEXT, zip_name TEXT, secret TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL);
CREATE TABLE licenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, plugin TEXT NOT NULL,
  mid TEXT, code TEXT, status TEXT NOT NULL, source TEXT NOT NULL, deact_count INTEGER NOT NULL DEFAULT 0,
  last_deact_at TEXT, order_id INTEGER, created_at TEXT NOT NULL, activated_at TEXT);
CREATE TABLE deactivations (id INTEGER PRIMARY KEY AUTOINCREMENT, license_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL, mid TEXT, reason TEXT NOT NULL, confirmed INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE videos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, file_id TEXT NOT NULL,
  created_at TEXT NOT NULL);
"""


@override_settings(LIC_SECRET="TTsecret")
class MigrationTest(TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        c = sqlite3.connect(self.path)
        c.executescript(OLD_SCHEMA)
        c.executemany("INSERT INTO plugins VALUES (?,?,?,?,?,?,?,?,?)", [
            ("TT", "Tez-Tez", "Taxlash", "150 000 so'm", "f1", "TT.zip", "TTsecret", 1, "2026-10-01 10:00"),
            ("MB", "Manga Bitmap", "", "90 000 so'm", None, None, "MBsecret", 1, "2026-10-02 10:00"),
        ])
        c.executemany("INSERT INTO users VALUES (?,?,?,?,?)", [
            (111, "ali", "Ali", "+998901112233", "2026-10-01 11:00"),
            (222, None, "Vali", "998 93 555 44 33", "2026-10-01 12:00"),
        ])
        code = L.activation_code("TT", "K7QM-3XPA", "TTsecret")
        c.executemany("INSERT INTO licenses (id,user_id,plugin,mid,code,status,source,deact_count,last_deact_at,"
                      "order_id,created_at,activated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
            (1, 111, "TT", "K7QM-3XPA", code, "faol", "xarid", 1, "2026-10-05 09:00", 3, "2026-10-03 10:00",
             "2026-10-05 10:00"),
            (2, 222, "MB", None, None, "bosh", "admin", 0, None, None, "2026-10-04 10:00", None),
            (3, 222, "TT", None, None, "eski", "eski", 0, None, 2, "2026-10-04 11:00", None),
        ])
        # 3-litsenziyada holat noma'lum ("eski") -> bo'sh bo'lib ko'chishi kerak
        c.execute("INSERT INTO deactivations VALUES (1,1,111,'AAAA-BBBB','Windows qayta o''rnatildi',1,"
                  "'2026-10-05 09:00')")
        c.executemany("INSERT INTO orders (id,user_id,name,phone,machine_code,status,password,created_at,plugin) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", [
            (1, 333, "Eski Mijoz", "+998977777777", "ZZZZ-2222", "tasdiqlandi", "TZ-AAAA", "2026-09-01 10:00", None),
            (2, 222, "Vali", "+998935554433", "YYYY-3333", "tasdiqlandi", "TZ-BBBB", "2026-09-02 10:00", None),
            (3, 111, "Ali", "+998901112233", "K7QM-3XPA", "tasdiqlandi", "TT-...", "2026-10-03 10:00", "TT"),
            (4, 111, "Ali", "+998901112233", "AAAA-CCCC", "kutilmoqda", None, "2026-10-06 10:00", "TT"),
            (5, 444, "Rad", "+998900000000", "XXXX-4444", "rad_etildi", None, "2026-09-03 10:00", None),
        ])
        c.commit()
        c.close()

    def tearDown(self):
        os.remove(self.path)

    def run_cmd(self):
        out = io.StringIO()
        call_command("eski_bazani_kochir", self.path, stdout=out)
        return out.getvalue()

    def test_import_and_idempotent(self):
        # saytda allaqachon ro'yxatdan o'tgan Ali - darhol ulanadi
        ali = User.objects.create_user("998901112233", password="x", phone="+998901112233", name="Ali")
        out = self.run_cmd()
        self.assertIn("tekshirilmagan to'lov", out)

        tt, mb = Plugin.objects.get(prefix="TT"), Plugin.objects.get(prefix="MB")
        self.assertEqual((tt.secret, tt.price), ("TTsecret", 150000))
        self.assertEqual((mb.secret, mb.price), ("MBsecret", 90000))
        self.assertEqual(LegacyCustomer.objects.count(), 4)        # 111, 222 + orders'dagi 333, 444
        self.assertEqual(LegacyCustomer.objects.get(telegram_id=222).phone, "+998935554433")

        lic = License.objects.get(legacy_id=1)
        self.assertEqual((lic.user, lic.status, lic.mid, lic.deact_count), (ali, License.FAOL, "K7QM-3XPA", 1))
        self.assertEqual(S.request_activation(ali, tt, "K7QM-3XPA").kind, S.CODE)   # eski kod ishlayveradi
        self.assertEqual(Deactivation.objects.get().license, lic)
        self.assertEqual(License.objects.get(legacy_id=3).status, License.BOSH)

        # TZ- buyurtmalar: 1 (o'tkazilmagan), 2 (botda o'tkazilgan -> 3-litsenziyaga bog'langan); rad etilgan yo'q
        self.assertEqual(LegacyTzOrder.objects.count(), 2)
        self.assertIsNone(LegacyTzOrder.objects.get(legacy_id=1).license)
        self.assertEqual(LegacyTzOrder.objects.get(legacy_id=2).license, License.objects.get(legacy_id=3))

        # takror ishga tushirish - dublikat yo'q
        self.run_cmd()
        self.assertEqual(License.objects.count(), 3)
        self.assertEqual(LegacyTzOrder.objects.count(), 2)
        self.assertEqual(Deactivation.objects.count(), 1)

        # Vali keyin ro'yxatdan o'tadi -> MB va TT litsenziyalari unga o'tadi
        vali = User.objects.create_user("998935554433", password="x", phone="+998935554433", name="Vali")
        self.assertEqual(S.claim_legacy(vali), 2)
        self.assertEqual(S.request_activation(vali, mb, "K7QM-3XPA").kind, S.BOUND)
        # eski TZ- xaridni boshqa odam ham ololmaydi, chunki botda allaqachon o'tkazilgan
        self.assertIn("allaqachon", S.claim_tz(ali, "YYYY-3333")[1])

    def test_secret_conflict(self):
        tt = Plugin.objects.create(prefix="TT", name="Tez-Tez", slug="tez-tez", price=1, secret="boshqa")
        u = User.objects.create_user("u", password="x", phone="+998900000009", name="U")
        License.objects.create(user=u, plugin=tt, status=License.BOSH)
        with self.assertRaises(CommandError):
            self.run_cmd()

    def test_not_a_bot_db(self):
        c = sqlite3.connect(self.path)
        c.execute("DROP TABLE orders")
        c.commit()
        c.close()
        with self.assertRaises(CommandError):
            self.run_cmd()
