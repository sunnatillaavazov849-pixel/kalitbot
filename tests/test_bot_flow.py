"""Botning to'liq oqimi Telegram'siz: soxta sessiya bilan update'lar yuboriladi.

Ro'yxatdan o'tish -> so'rov ID -> chek -> admin tasdig'i -> kod -> ko'chirish -> yangi PC (to'lovsiz)
-> eski TZ- litsenziya -> admin plagin qo'shishi.
"""
import asyncio
import os
import tempfile
import unittest
from datetime import datetime

_tmp = tempfile.mkdtemp()
os.environ.update(BOT_TOKEN="123456:TEST", ADMIN_IDS="1", LIC_SECRET="TestSecret_123",
                  DB_PATH=os.path.join(_tmp, "t.db"), PRICE="100 000 so'm")

from aiogram import Bot  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.types import (CallbackQuery, Chat, Contact, Document, Message, PhotoSize,  # noqa: E402
                           Update, User)

import bot as botmod  # noqa: E402
import db as dbm  # noqa: E402
from handlers.common import db  # noqa: E402
from handlers.keyboards import BTN_LEGACY, BTN_TRANSFER  # noqa: E402
from litsenziya import activation_code, deact_confirm  # noqa: E402

ADMIN, USER = 1, 100


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if method.__returning__ is Message:
            return Message(message_id=len(self.calls), date=datetime.now(),
                           chat=Chat(id=getattr(method, "chat_id", 0) or 0, type="private"),
                           text=getattr(method, "text", None) or getattr(method, "caption", None))
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


class Flow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        botmod.seed()
        cls.session = FakeSession()
        cls.bot = Bot("123456:TEST", session=cls.session)
        cls.dp = botmod.build_dispatcher()
        cls.n = 0
        cls.loop = asyncio.new_event_loop()

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def feed(self, uid=USER, text=None, photo=False, contact=None, document=None, callback=None):
        Flow.n += 1
        user = User(id=uid, is_bot=False, first_name="T", username=f"u{uid}")
        chat = Chat(id=uid, type="private")
        msg = Message(
            message_id=Flow.n, date=datetime.now(), chat=chat, from_user=user, text=text,
            photo=[PhotoSize(file_id="PHOTO", file_unique_id="p", width=1, height=1)] if photo else None,
            contact=Contact(phone_number=contact, first_name="T", user_id=uid) if contact else None,
            document=document,
        )
        if callback:
            upd = Update(update_id=Flow.n, callback_query=CallbackQuery(
                id=str(Flow.n), from_user=user, chat_instance="c", data=callback, message=msg))
        else:
            upd = Update(update_id=Flow.n, message=msg)
        start = len(self.session.calls)
        self.loop.run_until_complete(self.dp.feed_update(self.bot, upd))
        return self.session.calls[start:]

    @staticmethod
    def texts(calls, chat_id=None):
        out = []
        for c in calls:
            t = getattr(c, "text", None) or getattr(c, "caption", None)
            if t and (chat_id is None or getattr(c, "chat_id", None) == chat_id):
                out.append(t)
        return "\n".join(out)

    def test_full_flow(self):
        secret = db.get_plugin("TT")["secret"]
        self.assertEqual(secret, "TestSecret_123")

        # ro'yxatdan o'tish
        self.assertIn("Ismingizni", self.texts(self.feed(text="/start")))
        self.feed(text="Ali")
        self.assertIn("Ro'yxatdan o'tdingiz", self.texts(self.feed(contact="998901112233")))
        self.assertEqual(db.get_user(USER)["phone"], "+998901112233")

        # so'rov ID (kichik harf, probel bilan) -> to'lov
        self.assertIn("chek rasmini", self.texts(self.feed(text="tt k7qm 3xpa")))
        calls = self.feed(photo=True)
        self.assertTrue(any(type(c).__name__ == "SendPhoto" and c.chat_id == ADMIN for c in calls))
        order = db.recent(1)[0]
        self.assertEqual((order["plugin"], order["machine_code"]), ("TT", "K7QM-3XPA"))

        # foydalanuvchi o'zi tasdiqlay olmaydi
        self.feed(callback=f"ok:{order['id']}")
        self.assertEqual(db.get(order["id"])["status"], dbm.KUTILMOQDA)

        # admin tasdiqlaydi -> kod
        code = activation_code("TT", "K7QM-3XPA", secret)
        out = self.texts(self.feed(uid=ADMIN, callback=f"ok:{order['id']}"), chat_id=USER)
        self.assertIn(code, out)
        lic = db.user_licenses(USER, "TT")[0]
        self.assertEqual((lic["status"], lic["mid"], lic["code"]), (dbm.FAOL, "K7QM-3XPA", code))

        # o'sha so'rov qayta -> kod qayta beriladi, yangi buyurtma yo'q
        self.assertIn(code, self.texts(self.feed(text="TT-K7QM-3XPA")))
        self.assertEqual(len(db.recent(10)), 1)

        # boshqa PC: avval ko'chirish taklif qilinadi
        self.assertIn("boshqa kompyuterda", self.texts(self.feed(text="TT-AAAA-BBBB")))

        # ko'chirish: sabab -> noto'g'ri kod -> to'g'ri tasdiq kodi
        self.feed(text=BTN_TRANSFER)
        self.assertIn("Nima bo'ldi", self.texts(self.feed(callback=f"tr:{lic['id']}")))
        self.assertIn("tasdiq kodini", self.texts(self.feed(text="Windows qayta o'rnatildi")))
        self.assertIn("noto'g'ri", self.texts(self.feed(text="AAAA-AAAA")))
        out = self.texts(self.feed(text=deact_confirm(code, "K7QM-3XPA").lower()))
        self.assertIn("bo'shatildi", out)
        self.assertEqual(db.get_license(lic["id"])["status"], dbm.BOSH)

        # yangi PC -> to'lovsiz kod
        code2 = activation_code("TT", "AAAA-BBBB", secret)
        self.assertIn(code2, self.texts(self.feed(text="TT-AAAA-BBBB")))
        self.assertEqual(db.get_license(lic["id"])["mid"], "AAAA-BBBB")

        # shu kuni yana ko'chirish -> rad
        self.assertIn("allaqachon", self.texts(self.feed(callback=f"tr:{lic['id']}")))

        # eski TZ- litsenziya
        db.conn.execute(
            "INSERT INTO orders (user_id, name, phone, machine_code, status, created_at)"
            " VALUES (?, 'Ali', '+998', 'ZZZZ-2222', 'tasdiqlandi', '2026-01-01')", (USER,))
        db.conn.commit()
        self.feed(text=BTN_LEGACY)
        self.assertIn("o'tkazildi", self.texts(self.feed(text="zzzz2222")))
        self.assertTrue(any(l["source"] == dbm.ESKI for l in db.user_licenses(USER)))
        self.assertIn("allaqachon", self.texts(self.feed(text=BTN_LEGACY) + self.feed(text="ZZZZ-2222")))

        # admin: yangi plagin
        self.feed(uid=ADMIN, text="/plagin_qosh")
        self.feed(uid=ADMIN, text="mb")
        self.feed(uid=ADMIN, text="Manga Bitmap")
        self.feed(uid=ADMIN, text="150 000 so'm")
        self.feed(uid=ADMIN, text="-")
        doc = Document(file_id="ZIPID", file_unique_id="z", file_name="mb.zip")
        out = self.texts(self.feed(uid=ADMIN, document=doc))
        mb = db.get_plugin("MB")
        self.assertIn(mb["secret"], out)
        self.assertEqual(mb["zip_file_id"], "ZIPID")

        # oddiy foydalanuvchiga admin buyruqlari ishlamaydi
        self.assertNotIn("Admin buyruqlari", self.texts(self.feed(text="/admin")))
        self.assertIn("Admin buyruqlari", self.texts(self.feed(uid=ADMIN, text="/admin")))

        # yangi plagin uchun so'rov ID tanildi
        self.assertIn("Manga Bitmap", self.texts(self.feed(text="MB-AAAA-BBBB")))


if __name__ == "__main__":
    unittest.main()
