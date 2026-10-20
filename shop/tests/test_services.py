"""Biznes mantiq: so'rov kodi holatlari, tasdiqlash, kompyuter almashtirish cheklovlari, eski mijozlar."""
import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from shop import licensing as L
from shop import services as S
from shop.models import LegacyCustomer, LegacyTzOrder, License, Order, Plugin

TMP = tempfile.mkdtemp()


def receipt():
    return SimpleUploadedFile("chek.jpg", b"\xff\xd8\xff fake", content_type="image/jpeg")


@override_settings(PRIVATE_ROOT=TMP + "/private", MEDIA_ROOT=TMP + "/media")
class ServicesTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        self.tt = Plugin.objects.create(prefix="TT", name="Tez-Tez", slug="tez-tez", price=100000, secret="sec")
        self.user = User.objects.create_user("998901112233", password="x", phone="+998901112233", name="Ali")

    def buy(self, mid):
        order = S.create_order(self.user, self.tt, mid, receipt())
        return S.approve_order(order.pk)

    def test_purchase_flow_and_codes(self):
        self.assertEqual(S.request_activation(self.user, self.tt, "K7QM-3XPA").kind, S.NEED_PAYMENT)
        order = S.create_order(self.user, self.tt, "K7QM-3XPA", receipt())
        self.assertEqual(order.amount, 100000)
        self.assertEqual(S.request_activation(self.user, self.tt, "K7QM-3XPA").kind, S.PENDING)

        approved = S.approve_order(order.pk)
        lic = approved.license
        self.assertEqual(lic.code, L.activation_code("TT", "K7QM-3XPA", "sec"))
        self.assertEqual((lic.status, lic.user), (License.FAOL, self.user))
        self.assertIsNone(S.approve_order(order.pk))          # takror tasdiqlanmaydi
        self.assertIsNone(S.reject_order(order.pk))

        res = S.request_activation(self.user, self.tt, "K7QM-3XPA")
        self.assertEqual((res.kind, res.license), (S.CODE, lic))
        res = S.request_activation(self.user, self.tt, "AAAA-BBBB")
        self.assertEqual((res.kind, res.license), (S.ACTIVE_ELSEWHERE, lic))

    def test_reject(self):
        order = S.create_order(self.user, self.tt, "K7QM-3XPA", receipt())
        self.assertEqual(S.reject_order(order.pk, "chek ko'rinmaydi").admin_note, "chek ko'rinmaydi")
        self.assertEqual(S.request_activation(self.user, self.tt, "K7QM-3XPA").kind, S.NEED_PAYMENT)
        self.assertFalse(License.objects.exists())

    def test_parse_request(self):
        Plugin.objects.create(prefix="MB", name="Manga", slug="manga", price=1, secret="s2")
        self.assertEqual(S.parse_request("tt k7qm3xpa", self.tt), ("K7QM-3XPA", None))
        mid, err = S.parse_request("MB-K7QM-3XPA", self.tt)
        self.assertIsNone(mid)
        self.assertIn("boshqa plagin", err)
        self.assertIsNone(S.parse_request("TT-K7QM-3XP0", self.tt)[0])

    def test_transfer_limits(self):
        lic = self.buy("K7QM-3XPA").license
        start = timezone.now()
        mids = ["AAAA-BBBB", "CCCC-DDDD", "EEEE-FFFF"]
        for i, new_mid in enumerate(mids):
            with mock.patch("django.utils.timezone.now", return_value=start + timedelta(days=i)):
                lic.refresh_from_db()
                self.assertIsNone(S.deact_check(lic))
                confirm = L.deact_confirm(lic.code, lic.mid)
                self.assertTrue(S.confirm_matches(lic, confirm.lower()))
                self.assertFalse(S.confirm_matches(lic, "AAAA-AAAA"))
                self.assertIsNotNone(S.deactivate(lic.pk, "Windows qayta o'rnatildi", confirmed=True))
                res = S.request_activation(self.user, self.tt, new_mid)    # bo'sh -> to'lovsiz
                self.assertEqual(res.kind, S.BOUND)
                self.assertEqual(res.license.code, L.activation_code("TT", new_mid, "sec"))
                lic.refresh_from_db()
                self.assertEqual(S.deact_check(lic), "bugun")               # kuniga 1 marta
                self.assertIsNone(S.deactivate(lic.pk, "yana", confirmed=False))
        with mock.patch("django.utils.timezone.now", return_value=start + timedelta(days=10)):
            lic.refresh_from_db()
            self.assertEqual(lic.deact_count, 3)
            self.assertEqual(S.deact_check(lic), "limit")                   # 4-urinish
        S.block(lic)
        self.assertEqual(S.request_activation(self.user, self.tt, "ZZZZ-2222").kind, S.BLOCKED)
        self.assertTrue(S.unblock(lic.pk))
        lic.refresh_from_db()
        self.assertEqual((lic.status, lic.deact_count), (License.BOSH, 0))
        self.assertEqual(lic.deactivations.count(), 3)

    def test_claim_legacy_by_phone(self):
        lc = LegacyCustomer.objects.create(telegram_id=555, name="Vali", phone="+998907770000")
        License.objects.create(legacy_owner=lc, plugin=self.tt, mid="K7QM-3XPA",
                               code=L.activation_code("TT", "K7QM-3XPA", "sec"), status=License.FAOL,
                               source=License.ESKI)
        other = User.objects.create_user("998907770000", password="x", phone="+998907770000", name="Vali")
        self.assertEqual(S.claim_legacy(self.user), 0)
        self.assertEqual(S.claim_legacy(other), 1)
        self.assertEqual(S.claim_legacy(other), 0)                          # takror emas
        other.refresh_from_db()
        self.assertEqual(other.legacy_telegram_id, 555)
        self.assertEqual(S.request_activation(other, self.tt, "K7QM-3XPA").kind, S.CODE)

    def test_claim_tz(self):
        LegacyTzOrder.objects.create(machine_code="ZZZZ-2222", name="Ali", phone="+998", password="TZ-1")
        lic, err = S.claim_tz(self.user, "zzzz 2222")
        self.assertEqual(err, "")
        self.assertEqual((lic.status, lic.source), (License.BOSH, License.ESKI))
        self.assertIn("allaqachon", S.claim_tz(self.user, "ZZZZ-2222")[1])
        self.assertIn("topilmadi", S.claim_tz(self.user, "YYYY-3333")[1])
        self.assertEqual(S.request_activation(self.user, self.tt, "K7QM-3XPA").kind, S.BOUND)

    def test_secret_defaults(self):
        with self.settings(LIC_SECRET="TezTezKalit"):
            Plugin.objects.all().delete()
            self.assertEqual(Plugin.objects.create(prefix="tt", name="T", slug="t", price=1).secret, "TezTezKalit")
            mb = Plugin.objects.create(prefix="MB", name="M", slug="m", price=1)
            self.assertEqual(len(mb.secret), 32)
            self.assertNotEqual(mb.secret, "TezTezKalit")

    def test_order_is_per_user(self):
        other = User.objects.create_user("998900000000", password="x", phone="+998900000000", name="B")
        S.create_order(other, self.tt, "K7QM-3XPA", receipt())
        self.assertEqual(S.request_activation(self.user, self.tt, "K7QM-3XPA").kind, S.NEED_PAYMENT)
        self.assertEqual(Order.objects.count(), 1)
