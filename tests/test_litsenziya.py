"""Python porti VBA (Double arifmetikasi) bilan bir xil natija berishini tekshiradi.

Ishga tushirish: python -m unittest discover tests
"""
import math
import random
import unittest

import litsenziya as L

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
