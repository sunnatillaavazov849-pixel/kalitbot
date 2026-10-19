"""Baza mantiqi: ko'chirish cheklovlari, bo'sh litsenziya, eski buyurtma migratsiyasi."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import db as dbm


class TestDB(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db = dbm.DB(self.path)
        self.db.add_plugin("TT", "Tez-Tez", "100", secret="s")
        self.db.save_user(1, "u", "Ali", "+998901112233")

    def tearDown(self):
        self.db.conn.close()
        os.remove(self.path)

    def test_deactivation_limits(self):
        lic = self.db.create_license(1, "TT", dbm.XARID, "AAAA-BBBB", "TT-CODE")
        for i in range(dbm.MAX_DEACT):
            day = f"2026-01-0{i + 1}"
            with mock.patch.object(dbm, "today", return_value=day), \
                 mock.patch.object(dbm, "now", return_value=day + " 10:00"):
                self.assertIsNone(self.db.deact_check(self.db.get_license(lic)))
                self.assertTrue(self.db.deactivate(lic, "sabab", confirmed=True))
                self.assertEqual(self.db.get_license(lic)["status"], dbm.BOSH)
                # shu kuni ikkinchi marta: avval qayta bog'lab ko'ramiz
                self.assertTrue(self.db.bind_license(lic, "CCCC-DDDD", "TT-NEW"))
                self.assertEqual(self.db.deact_check(self.db.get_license(lic)), "bugun")
                self.assertFalse(self.db.deactivate(lic, "yana", confirmed=False))
        # 4-urinish - limit
        with mock.patch.object(dbm, "today", return_value="2026-02-01"):
            self.assertEqual(self.db.deact_check(self.db.get_license(lic)), "limit")
        self.db.block_license(lic)
        self.assertEqual(self.db.get_license(lic)["status"], dbm.BLOKLANGAN)
        self.assertTrue(self.db.unblock(lic))
        l = self.db.get_license(lic)
        self.assertEqual((l["status"], l["deact_count"]), (dbm.BOSH, 0))
        self.assertEqual(len(self.db.conn.execute("SELECT * FROM deactivations").fetchall()), dbm.MAX_DEACT)

    def test_bind_only_free(self):
        lic = self.db.create_license(1, "TT", dbm.ADMIN)
        self.assertEqual(self.db.get_license(lic)["status"], dbm.BOSH)
        self.assertTrue(self.db.bind_license(lic, "AAAA-BBBB", "X"))
        self.assertFalse(self.db.bind_license(lic, "CCCC-DDDD", "Y"))

    def test_legacy_migration_of_old_db(self):
        # eski bot bazasi: plugin/license_id ustunlarisiz
        self.db.conn.close()
        os.remove(self.path)
        conn = sqlite3.connect(self.path)
        conn.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,"
            " username TEXT, name TEXT NOT NULL, phone TEXT NOT NULL, machine_code TEXT NOT NULL,"
            " kind TEXT NOT NULL DEFAULT 'yangi', receipt_file_id TEXT, status TEXT NOT NULL DEFAULT"
            " 'kutilmoqda', password TEXT, created_at TEXT NOT NULL, decided_at TEXT)"
        )
        conn.execute(
            "INSERT INTO orders (user_id, name, phone, machine_code, status, password, created_at)"
            " VALUES (5, 'Vali', '+998', 'K7QM-3XPA', 'tasdiqlandi', 'TZ-1', '2026-01-01')"
        )
        conn.commit()
        conn.close()
        self.db = dbm.DB(self.path)
        o = self.db.legacy_order("K7QM-3XPA")
        self.assertIsNotNone(o)
        self.assertFalse(self.db.legacy_migrated(o["id"]))
        self.db.create_license(5, "TT", dbm.ESKI, order_id=o["id"])
        self.assertTrue(self.db.legacy_migrated(o["id"]))


if __name__ == "__main__":
    unittest.main()
