"""Saytning to'liq oqimi Django test mijozi bilan."""
import io
import json
import shutil
import tempfile
import zipfile
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from shop import licensing as L
from shop.models import LegacyCustomer, License, Order, Plugin

TMP = tempfile.mkdtemp()


@override_settings(PRIVATE_ROOT=TMP + "/private", MEDIA_ROOT=TMP + "/media", SITE_URL="https://sunat.test")
class SiteFlowTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        self.tt = Plugin.objects.create(prefix="TT", name="Tez-Tez", slug="tez-tez", price=150000, secret="sec",
                                        tagline="Taxlash plagini", version="2.0")
        self.tt.gms_file.save("TezTez.gms", ContentFile(b"gms-ichi"))
        self.admin = User.objects.create_superuser("admin", password="AdminPass1", phone="+998900000001", name="Admin")

    def register(self, phone="+998 90 111 22 33", name="Ali"):
        return self.client.post(reverse("royxat"), {"name": name, "phone": phone, "password": "Parol123x",
                                                    "password2": "Parol123x"})

    def test_public_pages(self):
        for name, args in [("home", []), ("plugin", ["tez-tez"]), ("app", []), ("help", []),
                           ("kirish", []), ("royxat", [])]:
            r = self.client.get(reverse(name, args=args))
            self.assertEqual(r.status_code, 200, name)
        self.assertContains(self.client.get("/"), "150 000")
        r = self.client.get(reverse("api_plugins"))
        data = json.loads(r.content)
        self.assertEqual(data["plugins"][0]["prefix"], "TT")
        self.assertEqual(data["plugins"][0]["buy_url"], "https://sunat.test/sotib-olish/tez-tez/")
        self.assertNotIn("secret", r.content.decode())

    def test_full_purchase_flow(self):
        # mehmon -> kirish sahifasiga
        r = self.client.get(reverse("buy", args=["tez-tez"]))
        self.assertRedirects(r, reverse("kirish") + "?next=" + reverse("buy", args=["tez-tez"]))

        self.assertRedirects(self.register(), reverse("kabinet"))
        user = User.objects.get(phone="+998901112233")

        # dasturdan kelgan havola: kod oldindan to'ldirilgan
        r = self.client.get(reverse("buy", args=["tez-tez"]) + "?kod=TT-K7QM-3XPA")
        self.assertContains(r, 'value="TT-K7QM-3XPA"')
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "code", "code": "MB-K7QM-3XPA"})
        self.assertContains(r, "So&#x27;rov kodi noto&#x27;g&#x27;ri")
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "code", "code": "tt k7qm 3xpa"})
        self.assertContains(r, "Chekni yuborish")
        self.assertContains(r, "150 000")

        # noto'g'ri fayl turi
        bad = SimpleUploadedFile("chek.exe", b"x")
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "pay", "receipt": bad})
        self.assertContains(r, "JPG")
        r = self.client.post(reverse("buy", args=["tez-tez"]),
                             {"step": "pay", "receipt": SimpleUploadedFile("chek.jpg", b"\xff\xd8img")})
        order = Order.objects.get()
        self.assertRedirects(r, reverse("order", args=[order.pk]))
        self.assertContains(self.client.get(reverse("order", args=[order.pk])), "tekshirilmoqda")

        # chek faqat adminga ko'rinadi
        self.assertEqual(self.client.get(reverse("staff_receipt", args=[order.pk])).status_code, 302)

        # admin tasdiqlaydi (admin panel tugmasi orqali)
        admin = self.client_class()
        admin.login(username="admin", password="AdminPass1")
        r = admin.get(reverse("staff_receipt", args=[order.pk]))
        self.assertEqual(b"".join(r.streaming_content), b"\xff\xd8img")
        r = admin.get(reverse("admin:shop_order_change", args=[order.pk]))
        self.assertContains(r, "Tasdiqlash")
        self.assertContains(r, "Kutilayotgan to'lovlar: 1")
        admin.post(reverse("admin:shop_order_change", args=[order.pk]), {"_approve": "1", "admin_note": ""})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.TASDIQLANDI)

        code = L.activation_code("TT", "K7QM-3XPA", "sec")
        self.assertContains(self.client.get(reverse("order", args=[order.pk])), code)
        r = self.client.get(reverse("kabinet"))
        self.assertContains(r, code)
        self.assertContains(r, "Kompyuterni almashtirish")

        # ZIP: manifest + gms; begona foydalanuvchi yuklay olmaydi
        lic = License.objects.get()
        r = self.client.get(reverse("download", args=[lic.pk]))
        z = zipfile.ZipFile(io.BytesIO(r.content))
        self.assertEqual(z.read("plagin/TezTez.gms"), b"gms-ichi")
        manifest = json.loads(z.read("plagin/manifest.json"))
        self.assertEqual((manifest["prefix"], manifest["files"]), ("TT", ["TezTez.gms"]))
        other = self.client_class()
        other.post(reverse("royxat"), {"name": "B", "phone": "+998907770000", "password": "Parol123x",
                                       "password2": "Parol123x"})
        self.assertEqual(other.get(reverse("download", args=[lic.pk])).status_code, 404)
        self.assertEqual(other.get(reverse("order", args=[order.pk])).status_code, 404)
        self.assertEqual(other.get(reverse("transfer", args=[lic.pk])).status_code, 404)

        # o'sha so'rov kodi qayta -> kod ko'rsatiladi, yangi to'lov so'ralmaydi
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "code", "code": "TT-K7QM-3XPA"})
        self.assertContains(r, code)

        # kompyuter almashtirish: noto'g'ri tasdiq -> xato, to'g'risi -> bo'sh, yangi PC'ga to'lovsiz
        url = reverse("transfer", args=[lic.pk])
        r = self.client.post(url, {"reason": "Windows qayta o'rnatildi", "confirm": "AAAA-AAAA"})
        self.assertContains(r, "Tasdiq kodi noto")
        r = self.client.post(url, {"reason": "Windows qayta o'rnatildi",
                                   "confirm": L.deact_confirm(code, "K7QM-3XPA")})
        self.assertRedirects(r, reverse("buy", args=["tez-tez"]))
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "code", "code": "TT-AAAA-BBBB"})
        self.assertContains(r, L.activation_code("TT", "AAAA-BBBB", "sec"))
        self.assertContains(r, "yangi kompyuterga o")
        self.assertContains(self.client.get(url), "Bugun allaqachon")
        self.assertEqual(Order.objects.count(), 1)

    def test_google_user_must_fill_profile(self):
        u = User.objects.create_user("g_user", password=None, name="", phone=None)
        self.client.force_login(u)
        r = self.client.get(reverse("buy", args=["tez-tez"]))
        self.assertTrue(r.url.startswith(reverse("profil")))
        LegacyCustomer.objects.create(telegram_id=1, name="Eski", phone="+998935554433")
        License.objects.create(legacy_owner=LegacyCustomer.objects.get(), plugin=self.tt, status=License.BOSH,
                               source=License.ESKI)
        r = self.client.post(reverse("profil") + "?next=/kabinet/", {"name": "Gulnora", "phone": "93 555 44 33"})
        self.assertRedirects(r, "/kabinet/")
        self.assertEqual(License.objects.get().user, u)
        self.assertContains(self.client.get("/kabinet/"), "So'rov kodini kiritish")

    def test_login_and_throttle(self):
        self.register()
        self.client.post(reverse("chiqish"))
        r = self.client.post(reverse("kirish"), {"phone": "901112233", "password": "Parol123x"})
        self.assertRedirects(r, reverse("kabinet"))
        self.client.post(reverse("chiqish"))
        for _ in range(10):
            self.client.post(reverse("kirish"), {"phone": "901112233", "password": "notogri"})
        r = self.client.post(reverse("kirish"), {"phone": "901112233", "password": "Parol123x"})
        self.assertContains(r, "Juda ko")

    def test_register_duplicate_phone(self):
        self.register()
        self.client.post(reverse("chiqish"))
        r = self.register(phone="998901112233")
        self.assertContains(r, "allaqachon ro")

    def test_legacy_tz_claim(self):
        from shop.models import LegacyTzOrder
        LegacyTzOrder.objects.create(machine_code="ZZZZ-2222", name="Ali", phone="+998", password="TZ-1")
        self.register()
        r = self.client.post(reverse("legacy_tz"), {"code": "zzzz2222"})
        self.assertRedirects(r, reverse("buy", args=["tez-tez"]))
        r = self.client.post(reverse("buy", args=["tez-tez"]), {"step": "code", "code": "TT-K7QM-3XPA"})
        self.assertContains(r, L.activation_code("TT", "K7QM-3XPA", "sec"))


GOOGLE = {"google": {"APPS": [{"client_id": "test-id.apps.googleusercontent.com", "secret": "s", "key": ""}],
                     "SCOPE": ["profile", "email"]}}


@override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE, GOOGLE_CLIENT_ID="test-id")
class GoogleLoginTest(TestCase):
    def test_button_and_redirect(self):
        r = self.client.get(reverse("kirish"))
        self.assertContains(r, "Google bilan kirish")
        r = self.client.post("/auth/google/login/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("accounts.google.com", r["Location"])
        self.assertIn("test-id.apps.googleusercontent.com", r["Location"])

    def test_hidden_without_keys(self):
        with override_settings(GOOGLE_CLIENT_ID=""):
            self.assertNotContains(self.client.get(reverse("kirish")), "Google bilan kirish")
