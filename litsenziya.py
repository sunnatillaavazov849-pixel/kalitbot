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


# =====================================================================
#  Yangi tizim: Sunat.cc Plaginlar mini ilovasi (ko'p plaginli)
#  Bu funksiyalar mini ilova (C#, SunatCore) va plaginlardagi
#  SunatLicense.bas bilan AYNAN bir xil ishlashi shart.
#  Tekshiruv namunalari: miniilova/testvectors.json
# =====================================================================

# Ochiq "tuz"lar: maxfiy emas, faqat natijalarni bir-biridan ajratadi
MID_SALT = "SunatCC|MID|v1"
OFF_SALT = "SunatCC|OFF|v1"
_PREFIX_RE = re.compile(r"^[A-Z]{2,4}$")


def clean(text: str) -> str:
    """Faqat lotin harf va raqamlar, katta harfda."""
    return re.sub(r"[^A-Za-z0-9]", "", text or "").upper()


def is_valid_prefix(prefix: str) -> bool:
    return bool(_PREFIX_RE.match(prefix or ""))


def normalize_hw(hw: str) -> str:
    """Uskuna satri: katta harf, faqat A-Z 0-9 ':' '-'."""
    return re.sub(r"[^A-Z0-9:\-]", "", (hw or "").upper())


def machine_id(hw: str) -> str:
    """Uskuna satridan (masalan `UUID:4C4C4544-...`) kompyuter ID: `XXXX-XXXX`."""
    c = _mix_code("mid|" + normalize_hw(hw), 8, MID_SALT)
    return f"{c[:4]}-{c[4:]}"


def check_char(s: str) -> str:
    """Ochiq nazorat belgisi: kodni xato yozishni ushlaydi (himoya emas)."""
    total = sum((i + 1) * ord(ch) for i, ch in enumerate(s))
    return PW_ALPHA[total % 32]


def activation_code(prefix: str, mid: str, secret: str) -> str:
    """Plagin + kompyuter ID uchun faollashtirish kodi: `TT-XXXX-XXXX-XXXC`."""
    seed = f"{prefix}|{mid}"
    body = _mix_code("act|" + seed, 8, secret) + _mix_code("act2|" + seed, 3, secret)
    body += check_char(prefix + body)
    return f"{prefix}-{body[0:4]}-{body[4:8]}-{body[8:12]}"


def code_format_ok(code: str, prefix: str) -> bool:
    """Kod ko'rinishi va nazorat belgisi to'g'rimi (maxfiy kalitsiz tekshiruv)."""
    s = clean(code)
    if not s.startswith(prefix) or len(s) != len(prefix) + 12:
        return False
    body = s[len(prefix):]
    if any(ch not in PW_ALPHA for ch in body):
        return False
    return body[11] == check_char(prefix + body[:11])


def deact_confirm(code: str, mid: str) -> str:
    """Mini ilova dezaktivatsiyada ko'rsatadigan tasdiq kodi: `XXXX-XXXX`."""
    c = _mix_code("off|" + clean(code) + "|" + mid, 8, OFF_SALT)
    return f"{c[:4]}-{c[4:]}"


def parse_request_id(text: str, prefixes) -> tuple[str, str] | None:
    """`TT-K7QM-3XPA` (defissiz/kichik harf ham) -> ("TT", "K7QM-3XPA")."""
    s = clean(text)
    for p in sorted(prefixes, key=len, reverse=True):
        rest = s[len(p):]
        if s.startswith(p) and len(rest) == 8 and all(ch in PW_ALPHA for ch in rest):
            return p, f"{rest[:4]}-{rest[4:]}"
    return None
