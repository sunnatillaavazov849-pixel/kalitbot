"""Tez-Tez parol algoritmi.

TezTezAdmin.bas dagi MakePassword / PwFor / MixCode / HashHex / HexVal
funksiyalarining Python'dagi aynan nusxasi. Bu yerdagi har bir o'zgarish
plagin bilan mos kelmay qolishiga olib keladi.

VBA'da HashHex Double bilan ishlaydi, lekin barcha oraliq qiymatlar
2^53 dan kichik (h < 2^31, h*257 + c < 2^40), shuning uchun natija
butun sonlardagi mod 2147483647 bilan aynan bir xil.
"""
import re

PW_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_P = 2147483647
_KOD_RE = re.compile(rf"^[{PW_ALPHA}]{{8}}$")


def _hash_hex(s: str) -> str:
    h1, h2 = 7, 13
    for ch in s:
        c = ord(ch)  # AscW (faqat ASCII belgilar ishlatiladi)
        h1 = (h1 * 131 + c) % _P
        h2 = (h2 * 257 + c + 1) % _P
    return f"{h1:08X}{h2:08X}"


def _hex_val(s: str) -> int:
    return int(s, 16)


def _mix_code(seed: str, n_chars: int, secret: str) -> str:
    h = _hash_hex(seed + "|" + secret)
    for _ in range(12):
        h = _hash_hex(h + "|" + secret + "|" + h[::-1] + seed)
    h = h + _hash_hex(h + secret)
    out = []
    for i in range(n_chars):
        # VBA: Mid$(h, i * 4 + 3, 2) -> 1-asosli indeks
        v = _hex_val(h[i * 4 + 2:i * 4 + 4]) % 32
        out.append(PW_ALPHA[v])
    return "".join(out)


def _pw_for(mc: str, secret: str) -> str:
    return _mix_code("pw|" + mc, 8, secret) + _mix_code("pw2|" + mc, 4, secret)


def make_password(machine_code: str, secret: str) -> str:
    """`XXXX-XXXX` kompyuter kodi uchun `TZ-XXXX-XXXX-XXXX` parol."""
    c = _pw_for(machine_code, secret)
    return f"TZ-{c[0:4]}-{c[4:8]}-{c[8:12]}"


def normalize_machine_code(text: str) -> str | None:
    """Foydalanuvchi yozgan kodni `XXXX-XXXX` ga keltiradi, noto'g'ri bo'lsa None."""
    s = re.sub(r"[^A-Za-z0-9]", "", text or "").upper()
    if not _KOD_RE.match(s):
        return None
    return f"{s[:4]}-{s[4:]}"
