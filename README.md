# Sunat.cc Plaginlar — Telegram bot + Windows mini ilova

CorelDRAW plaginlarini sotish va faollashtirish tizimi:

| Qism | Qayerda | Vazifasi |
|---|---|---|
| **Telegram bot** | shu repo (`bot.py`, `handlers/`) | katalog, to'lov, admin tasdig'i, faollashtirish kodlari, ko'chirish, o'rnatish videolari |
| **Mini ilova** `Sunat.cc Plaginlar.exe` | `miniilova/` | kompyuter ID, plaginni CorelDRAW'ga o'rnatish, kodni kiritish, dezaktivatsiya |
| **Plagin moduli** `SunatLicense.bas` | `corel_palgin` repo | plagin CorelDRAW'da ochilganda kodni tekshiradi |

## Mijoz yo'li
1. Bot: `/start` → ism, telefon → **🛒 Plaginlar** → ZIP yuklab oladi (ichida mini ilova + plagin).
2. Mini ilova: **Plagin qo'shish** → CorelDRAW versiyasi → O'rnatish → **so'rov ID** (`TT-K7QM-3XPA`).
3. Bot: so'rov ID → narx va karta → chek → admin ✅ → **kod** (`TT-XXXX-XXXX-XXXX`).
4. Mini ilova: kodni kiritadi → plagin faol.
5. Boshqa kompyuter: mini ilovada **Dezaktiv qilish** → tasdiq kodi → botda **🔄 Boshqa PC'ga ko'chirish**
   (sabab so'raladi) → yangi kompyuterning so'rov ID'si → kod **to'lovsiz**.
   Kuniga 1 marta, jami 3 marta; undan keyin litsenziya bloklanadi (admin `/blokdan_chiqar` qiladi).
6. Eski `TZ-` mijozlar: **♻️ Eski litsenziya** → eski kompyuter kodi → yangi tizimga bepul o'tadi.

## Botni o'rnatish
**Windows'da eng oson yo'l:** `ishga_tushirish.bat` ni ikki marta bosing. U kutubxonalarni o'rnatadi,
birinchi marta `.env` faylini yaratib Bloknotda ochadi, keyingi safar botni ishga tushiradi.

Qo'lda (Linux / VPS):
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # to'ldiring
python bot.py
```

| `.env` | Qayerdan |
|---|---|
| `BOT_TOKEN` | @BotFather → /newbot |
| `ADMIN_IDS` | @userinfobot (bir nechta bo'lsa vergul bilan) |
| `LIC_SECRET` | `TezTezAdmin.bas` dagi `LIC_SECRET` (Tez-Tez va eski `TZ-` parollar) |
| `PRICE`, `CARD_NUMBER`, `CARD_OWNER` | o'zingiz |

Birinchi ishga tushishda Tez-Tez (`TT`) plagini bazaga o'zi qo'shiladi.

> ⚠️ Repo **ommaviy**. `.env` va `teztez.db` GitHub'ga yuklanmaydi. Bazada boshqa plaginlarning
> maxfiy kalitlari saqlanadi — `teztez.db` nusxasini muntazam saqlab turing.

## Admin buyruqlari
`/admin` — to'liq ro'yxat. Asosiylari:
- `/plagin_qosh` — yangi plagin (belgi, nom, narx, tavsif, ZIP); bot maxfiy kalitni beradi;
- `/plagin_zip TT`, `/plagin_narx TT ...`, `/plagin_yoq TT`, `/plagin_kalit TT`;
- `/video_qosh`, `/videolar` — 📖 O'rnatish bo'limi videolari;
- `/litsenziyalar`, `/bloklangan`, `/blokdan_chiqar ID`, `/litsenziya_ber USER_ID TT`;
- `/kod TT-K7QM-3XPA` — kodni hisoblab ko'rish; `/royxat` — buyurtmalar; `/parol` — eski TZ- parol.

## Yangi plagin qo'shish (to'liq)
1. Botda `/plagin_qosh` → belgi (masalan `MB`) va boshqalar → bot **maxfiy kalit** beradi.
2. `corel_palgin` dagi `SunatLicense.bas` ni plaginga import qiling, `PLUGIN_PREFIX` va `LIC_SECRET` ni yozing,
   asosiy makros boshiga `If Not SunatCheck() Then Exit Sub`. `.gms` ni saqlang.
3. Mijoz ZIP'ini yasang:
   ```bash
   python tools/zip_yasash.py --prefix MB --name "Manga Bitmap" --gms MangaBitmap.gms \
       --exe "Sunat.cc Plaginlar.exe" --bot https://t.me/<bot_nomi>
   ```
4. Botda `/plagin_zip MB` → ZIP'ni yuboring.

## Mini ilova
- C# WPF, .NET Framework 4.8 (Windows 10/11 da bor), bitta `.exe`, interfeys XAML'siz (Linux'da ham yig'iladi).
- **Yuklab olish:** GitHub → **Actions** → "Mini ilova" → oxirgi muvaffaqiyatli ishga tushirish → **Artifacts**.
  `miniilova-v1.0.0` kabi teg qo'yilsa, **Releases** sahifasiga ham chiqadi.
- Qo'lda yig'ish: `dotnet build miniilova/SunatPlaginlar -c Release`.
- Kodni reyestrga yozadi: `HKCU\Software\SunatCC\Plaginlar\<PREFIKS>\Code`. Ichida maxfiy kalit yo'q.
- CorelDRAW'ni reyestr va `Program Files\Corel` dan topadi; standart joy — foydalanuvchi GMS papkasi
  (`%APPDATA%\Corel\...\Draw\GMS`), kerak bo'lsa dastur papkasi (administrator) yoki qo'lda tanlangan papka.

## Kodlar va tekshiruv
Bitta algoritm uch joyda: `litsenziya.py` (bot), `miniilova/SunatCore` (C#), `SunatLicense.bas` (VBA).
- `python -m unittest discover tests` — bot, baza, to'liq Telegram oqimi (soxta sessiya bilan), algoritm;
- `python tools/testvectors.py` → `miniilova/testvectors.json`;
- `dotnet run --project miniilova/SunatCore.Tests` — C# natijalari Python bilan bir xilmi;
- CorelDRAW'da `Alt+F8` → `SunatTekshiruv` — VBA natijalari va shu kompyuter ID'si.

**Cheklov:** tizim oflayn ishlaydi. Mijoz kompyuteridagi himoyani qat'iyatli odam buzishi mumkin;
ko'chirish cheklovlari va bazadagi tarix oddiy foydalanuvchilarni to'xtatadi.
