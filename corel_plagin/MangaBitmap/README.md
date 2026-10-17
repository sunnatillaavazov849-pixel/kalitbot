# Manga Bitmap — CorelDRAW plagini

Rasmlarni bir bosishda **bitmap** qiladi. Oynasi to'q kulrang, yozuvlari oq va qalin.

## Imkoniyatlar
| Bo'lim | Variantlar |
|---|---|
| **Qamrov** | Tanlangan obyektlar · Joriy list · Barcha listlar |
| **Obyektlar** | Faqat rasmlar (guruh va PowerClip ichidagilari ham) · Barcha obyektlar |
| **Usul** | Har birini alohida bitmap · Har bir listdagi hammasini **bitta** bitmap |
| **Rang rejimi** | RGB · CMYK · Kulrang |
| **Razreshenie** | 72 / 150 / 200 / 300 / 350 / 400 / 600 / 1200 yoki istalgan son (30–2400) |
| **Qo'shimcha** | Silliqlash (anti-aliasing) · Shaffof fon |
| **Yorqinlik** | Polzunok: chapga — to'qroq, o'ngga — ochroq (−100 … +100), `0` tugmasi qaytaradi |

- Hammasi **bitta Undo** (Ctrl+Z) bilan qaytariladi.
- Qulflangan obyektlar, yashirin va qulflangan qatlamlar o'tkazib yuboriladi.
- Sozlamalar eslab qolinadi (keyingi ochilishda shu holatda chiqadi).

## O'rnatish (bir marta)
1. CorelDRAW → **Tools › Scripts › Script Editor** (yoki **Alt+F11**) — VBA muharriri ochiladi.
2. Chap paneldan **GlobalMacros** (yoki o'zingizning `.gms` loyihangiz) ni tanlang.
3. **File › Import File…** → `MangaBitmap.bas` faylini tanlang.
4. **Insert › UserForm** — bo'sh forma paydo bo'ladi.
   Pastdagi **Properties** oynasida `(Name)` ni **`frmMangaBitmap`** ga o'zgartiring.
5. Formani o'ng tugma bilan bosib **View Code** ni tanlang, u yerdagi hamma narsani o'chirib,
   `frmMangaBitmap_kodi.txt` faylidagi **butun** kodni joylang.
6. **File › Save** (Ctrl+S) va muharrirni yoping.

> Formaga hech narsa chizish shart emas — barcha tugma va maydonlar kod orqali yaratiladi.

## Ishga tushirish
**Tools › Scripts › Run Script** (yoki *Macros › Run Macro*) → `MangaBitmapPlagin.MangaBitmap`.

Panelga tugma qo'yish: **Tools › Options › Customization › Commands** → ro'yxatdan
**Macros** ni tanlang → `MangaBitmapPlagin.MangaBitmap` ni asboblar paneliga sudrab qo'ying.
Shu joyda **Shortcut Keys** orqali tezkor tugma ham biriktirish mumkin.

## Yorqinlik qanday ishlaydi
Bitmap qilishdan oldin rasm ustiga oq (ochroq) yoki qora (to'qroq) shaffof qatlam qo'yiladi va
u bitmapga singib ketadi. Masalan `+20` — rasm 20% ochroq, `−15` — 15% to'qroq.
Qatlam rasmning to'rtburchak chegarasini qoplaydi, shuning uchun to'rtburchak bo'lmagan vektor
shakllarda fon ham ochroq/to'qroq bo'ladi (oddiy rasmlarda bu sezilmaydi).

## Talablar
CorelDRAW X4 va undan yangi (VBA o'rnatilgan bo'lishi kerak).
