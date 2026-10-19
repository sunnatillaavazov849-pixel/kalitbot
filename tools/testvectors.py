"""miniilova/testvectors.json ni yaratadi: Python, C# (SunatCore) va VBA (SunatLicense.bas)
bir xil natija berishini tekshirish uchun namunalar.

Ishga tushirish: python tools/testvectors.py
Maxfiy kalit sifatida faqat TEST qiymati ishlatiladi.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import litsenziya as L  # noqa: E402

TEST_SECRET = "TestSecret_NotReal_0123456789abc"

HW = [
    "UUID:4C4C4544-0042-3510-8051-B4C04F4A3732",
    "UUID:03AA02FC-0414-05E1-1F06-B70700080009",
    "BB:PF2ZXK8Q",
    "BB:/7XKD3M2/CNWS2008B800YX/",
    "PC:DESKTOP-9F3K2LM:1824371651",
    "pc:ofis-kompyuter:12",
]


# (uuid, ona plata seriyasi, kompyuter nomi, disk seriyasi)
CHOOSE = [
    ("4c4c4544-0042-3510-8051-b4c04f4a3732", "PF2ZXK8Q", "DESKTOP-1", 123),
    ("FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF", "PF2ZXK8Q", "DESKTOP-1", 123),
    ("00000000-0000-0000-0000-000000000000", " Default string ", "ofis-pc", -1824371651),
    ("03000200-0400-0500-0006-000700080009", "To be filled by O.E.M.", "Ofis-PC", 42),
    ("", "", "", 0),
    ("  ", "0000000", "PC2", 7),
]


def build():
    out = {"secret": TEST_SECRET, "choose": [], "machine_ids": [], "codes": [], "deact": []}
    for uuid, board, name, vol in CHOOSE:
        out["choose"].append({"uuid": uuid, "board": board, "name": name, "volume": vol,
                              "hw": L.choose_hw(uuid, board, name, vol)})
    for hw in HW:
        out["machine_ids"].append({"hw": hw, "mid": L.machine_id(hw)})
    for item in out["machine_ids"]:
        for prefix in ("TT", "MB", "ABCD"):
            code = L.activation_code(prefix, item["mid"], TEST_SECRET)
            out["codes"].append({"prefix": prefix, "mid": item["mid"], "code": code})
            out["deact"].append({"code": code, "mid": item["mid"], "confirm": L.deact_confirm(code, item["mid"])})
    return out


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "miniilova", "testvectors.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("yozildi:", os.path.normpath(path))
