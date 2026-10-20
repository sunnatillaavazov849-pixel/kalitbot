"""Python porti VBA (Double arifmetikasi) bilan bir xil natija berishini tekshiradi.

Ishga tushirish: python manage.py test
"""
import math
import random
import unittest

from shop import licensing as L

SECRET = "TestSecret_123abcXYZ"  # haqiqiy LIC_SECRET emas


def vba_hash_hex(s: str) -> str:
    """TezTezAdmin.bas dagi HashHex, Double (float) bilan qatorma-qator."""
    P = 2147483647.0
    h1, h2 = 7.0, 13.0
    for ch in s:
        c = float(ord(ch))
        if c < 0:
            c += 65536
        h1 = h1 * 131 + c
        h1 = h1 - math.floor(h1 / P) * P
        if h1 >= P:
            h1 -= P
        if h1 < 0:
            h1 += P
        h2 = h2 * 257 + c + 1
        h2 = h2 - math.floor(h2 / P) * P
        if h2 >= P:
            h2 -= P
        if h2 < 0:
            h2 += P
    # Hex$(Double) -> Long ga yaxlitlanadi (qiymatlar butun son)
    return ("00000000" + format(round(h1), "X"))[-8:] + ("00000000" + format(round(h2), "X"))[-8:]


class TestHash(unittest.TestCase):
    def test_hash_matches_vba_double(self):
        rnd = random.Random(1)
        chars = L.PW_ALPHA + "abcdefxyz|-0123456789"
        for _ in range(3000):
            s = "".join(rnd.choice(chars) for _ in range(rnd.randint(0, 200)))
            self.assertEqual(L._hash_hex(s), vba_hash_hex(s), s)

    def test_password_matches_vba_pipeline(self):
        orig = L._hash_hex
        try:
            rnd = random.Random(2)
            for _ in range(200):
                mc = "".join(rnd.choice(L.PW_ALPHA) for _ in range(8))
                mc = mc[:4] + "-" + mc[4:]
                L._hash_hex = orig
                a = L.make_password(mc, SECRET)
                L._hash_hex = vba_hash_hex
                b = L.make_password(mc, SECRET)
                self.assertEqual(a, b)
                self.assertRegex(a, r"^TZ-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$")
        finally:
            L._hash_hex = orig

    def test_depends_on_code_and_secret(self):
        self.assertNotEqual(L.make_password("K7QM-3XPA", SECRET), L.make_password("K7QM-3XPB", SECRET))
        self.assertNotEqual(L.make_password("K7QM-3XPA", SECRET), L.make_password("K7QM-3XPA", SECRET + "x"))


class TestNormalize(unittest.TestCase):
    def test_accepts_variants(self):
        for s in ["K7QM-3XPA", "k7qm3xpa", " k7qm 3xpa ", "K7QM–3XPA"]:
            self.assertEqual(L.normalize_machine_code(s), "K7QM-3XPA", s)

    def test_rejects_bad(self):
        for s in ["", "K7QM-3XP", "K7QM-3XPAA", "K0QM-3XPA", "K1QM-3XPA", "KOQM-3XPA", "KIQM-3XPA"]:
            self.assertIsNone(L.normalize_machine_code(s), s)


if __name__ == "__main__":
    unittest.main()


class TestNewScheme(unittest.TestCase):
    def test_codes_follow_vba_pipeline(self):
        orig = L._hash_hex
        try:
            for hw in ["UUID:4C4C4544-0042-3510-8051-B4C04F4A3732", "PC:DESKTOP-1:42"]:
                L._hash_hex = orig
                a = (L.machine_id(hw),)
                a += (L.activation_code("TT", a[0], SECRET), L.deact_confirm("TT-AAAA", a[0]))
                L._hash_hex = vba_hash_hex
                b = (L.machine_id(hw),)
                b += (L.activation_code("TT", b[0], SECRET), L.deact_confirm("TT-AAAA", b[0]))
                self.assertEqual(a, b)
        finally:
            L._hash_hex = orig

    def test_activation_code_format_and_check(self):
        code = L.activation_code("MB", "K7QM-3XPA", SECRET)
        self.assertRegex(code, r"^MB-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$")
        self.assertTrue(L.code_format_ok(code, "MB"))
        self.assertTrue(L.code_format_ok(code.lower().replace("-", " "), "MB"))
        self.assertFalse(L.code_format_ok(code, "TT"))
        broken = 0
        for i, ch in enumerate(code):
            if ch in L.PW_ALPHA and i > 2:
                other = "A" if ch != "A" else "B"
                broken += not L.code_format_ok(code[:i] + other + code[i + 1:], "MB")
        self.assertGreaterEqual(broken, 10)  # bitta belgi xatosi deyarli har doim ushlanadi

    def test_codes_differ(self):
        self.assertNotEqual(L.activation_code("TT", "K7QM-3XPA", SECRET), L.activation_code("MB", "K7QM-3XPA", SECRET))
        self.assertNotEqual(L.activation_code("TT", "K7QM-3XPA", SECRET), L.activation_code("TT", "K7QM-3XPB", SECRET))
        self.assertNotEqual(L.machine_id("UUID:1"), L.machine_id("UUID:2"))
        self.assertEqual(L.machine_id("uuid:abc-1"), L.machine_id("UUID:ABC-1 "))

    def test_parse_request_id(self):
        self.assertEqual(L.parse_request_id("tt-k7qm-3xpa", ["TT", "MB"]), ("TT", "K7QM-3XPA"))
        self.assertEqual(L.parse_request_id("ABCD K7QM3XPA", ["AB", "ABCD"]), ("ABCD", "K7QM-3XPA"))
        self.assertIsNone(L.parse_request_id("XX-K7QM-3XPA", ["TT"]))
        self.assertIsNone(L.parse_request_id("TT-K7QM-3XP0", ["TT"]))

    def test_testvectors_file_is_current(self):
        import json, os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
        import testvectors
        path = os.path.join(os.path.dirname(__file__), "..", "..", "miniilova", "testvectors.json")
        with open(path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), testvectors.build())
