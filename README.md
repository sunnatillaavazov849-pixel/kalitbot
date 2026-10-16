# Tez-Tez by Sunat.cc — Telegram bot

CorelDRAW uchun **Tez-Tez** plaginiga parol sotadigan bot.

## Bot nima qiladi
1. **/start** → ism → telefon (📱 tugma yoki yozib) → **kompyuter kodi** (`XXXX-XXXX`).
2. Narx va karta raqamini ko'rsatadi, **to'lov chekini** (rasm yoki PDF) so'raydi.
3. Chekni adminga yuboradi: ism, telefon, kompyuter kodi, chek + **✅ Tasdiqlash / ❌ Rad etish**.
4. Tasdiqlansa, foydalanuvchiga `TZ-XXXX-XXXX-XXXX` parol yuboriladi; rad etilsa — "To'lov tasdiqlanmadi".
5. **🔄 Qayta faollashtirish** (yoki /qayta): kompyuter kodi o'zgarganda — chek so'ralmaydi,
   admin tasdiqlasa yangi parol to'lovsiz beriladi. Adminga foydalanuvchining avval
   tasdiqlangan xaridi bor-yo'qligi ko'rsatiladi.
6. Barcha buyurtmalar SQLite bazada (`teztez.db`) saqlanadi.

**Admin buyruqlari:**
- `/royxat` — oxirgi 30 ta buyurtma va statistika;
- `/parol K7QM-3XPA` — buyurtmasiz parol hisoblash (tekshirish uchun).

Foydalanuvchi: `/bekor` — joriy jarayonni bekor qilish.

## O'rnatish
```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```
`.env` faylini to'ldiring:

| O'zgaruvchi | Qayerdan |
|---|---|
| `BOT_TOKEN` | @BotFather → /newbot |
| `ADMIN_IDS` | @userinfobot (bir nechta bo'lsa vergul bilan) |
| `LIC_SECRET` | `TezTezAdmin.bas` dagi `LIC_SECRET` qiymati |
| `PRICE`, `CARD_NUMBER`, `CARD_OWNER` | o'zingiz |

Ishga tushirish:
```bash
python bot.py
```

> ⚠️ Bu repozitoriy **ommaviy (public)**. `LIC_SECRET` va `BOT_TOKEN` faqat `.env` da
> turadi va u `.gitignore` da — hech qachon kodga yoki GitHub'ga yozmang.
> `LIC_SECRET` kimda bo'lsa, o'zi parol yarata oladi.

## Parol algoritmi
`litsenziya.py` — `TezTezAdmin.bas` dagi `MakePassword` / `PwFor` / `MixCode` /
`HashHex` / `HexVal` ning aynan nusxasi. Testlar VBA'ning Double arifmetikasini
qatorma-qator takrorlab, natija bir xilligini tekshiradi:
```bash
python -m unittest discover tests
```

**Haqiqiy tekshiruv:** CorelDRAW'da `Alt+F8 → TezTezParollar` ga 2–3 ta kompyuter kodi
kiritib, chiqqan parollarni botdagi `/parol <kod>` natijasi bilan solishtiring — aynan
bir xil bo'lishi shart.

## Hosting
Bot `polling` rejimida ishlaydi, ochiq port kerak emas: VPS, Railway/Render (worker),
yoki doim yoqiq kompyuter. Serverda `teztez.db` fayli saqlanib qolishi kerak
(Railway/Render'da doimiy disk — volume ulang).
