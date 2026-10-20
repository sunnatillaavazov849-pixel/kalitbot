# Sunat.cc Plaginlar — sayt + Windows dastur

CorelDRAW plaginlarini sotish va faollashtirish tizimi (Telegram botsiz).

| Qism | Qayerda | Vazifasi |
|---|---|---|
| **Sayt** (Django) | `sunat/`, `accounts/`, `shop/`, `templates/`, `static/` | ro'yxatdan o'tish (telefon yoki Google), katalog, to'lov (chek), kabinet, kompyuter almashtirish, admin panel |
| **Windows dastur** `SunatPlaginlar.exe` | `miniilova/` | plaginlar ro'yxati, so'rov kodi, plaginni CorelDRAW'ga o'rnatish, kod kiritish, dezaktivatsiya |
| **Plagin moduli** `SunatLicense.bas` | `corel_palgin` repo | plagin ichida kodni tekshiradi (kerak bo'lsa kod so'raydi) |

## Mijoz yo'li
1. Saytda ro'yxatdan o'tadi (telefon + parol yoki Google).
2. Windows dasturini yuklab oladi (o'rnatishsiz `.exe` yoki `setup.exe`).
3. Dasturda plaginni tanlaydi → **so'rov kodi** (`TT-K7QM-3XPA`) → "Saytda sotib olish" (kod saytga o'zi tushadi).
4. Saytda kartaga to'laydi, chekni yuklaydi → admin tasdiqlaydi → kabinetda **faollashtirish kodi** va plagin ZIP'i.
5. Dasturda "Plaginni o'rnatish" → ZIP → CorelDRAW versiyasi; kodni kiritadi → plagin ishlaydi.
6. Kompyuter almashsa: dasturda "Dezaktiv qilish" → tasdiq kodi → saytda "Kompyuterni almashtirish"
   (kuniga 1, jami 3 marta; keyin blok — admin blokdan chiqaradi) → yangi kompyuterda kod to'lovsiz.

## Kompyuterda sinash
**Windows'da eng oson:** `saytni_ochish.bat` ni ikki marta bosing — hammasini o'zi tayyorlaydi, namuna ma'lumot qo'shadi
va brauzerda `http://localhost:8000` ni ochadi (admin: `admin` / `admin12345`, faqat shu kompyuter uchun).

Qo'lda:
```bash
pip install -r requirements.txt
cp .env.example .env          # DEBUG=1 qiling
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver    # http://localhost:8000 , admin: /boshqaruv/
python manage.py test         # barcha testlar
```

## Serverga o'rnatish (Ubuntu VPS)
```bash
curl -fsSL https://raw.githubusercontent.com/sunnatillaavazov849-pixel/kalitbot/claude/practical-hawking-kbsu0h/deploy/ornatish.sh -o ornatish.sh
sudo bash ornatish.sh sunat.cc
```
Python, gunicorn, Caddy (HTTPS avtomatik), har kunlik zaxira (`/var/backups/sunat`) o'rnatiladi.
Yangilash: `sudo bash /opt/sunat/deploy/yangilash.sh`. Sozlamalar: `/opt/sunat/.env` (namuna: `.env.example`).

Eski Telegram bot bazasini ko'chirish (plaginlar kalitlari, mijozlar, litsenziyalar, eski TZ- xaridlar):
```bash
sudo -u sunat /opt/sunat/venv/bin/python /opt/sunat/manage.py eski_bazani_kochir /yo'l/teztez.db
```
Eski mijoz saytda o'sha telefon raqami bilan ro'yxatdan o'tsa, litsenziyalari o'zi ulanadi.

## Admin panel (`/boshqaruv/`)
- **Buyurtmalar:** chek rasmi, "Tasdiqlash" / "Rad etish" tugmalari; tepada kutilayotgan to'lovlar soni.
- **Plaginlar:** nom, narx, rasm, `.gms` fayl, versiya; **maxfiy kalit** yaratilganda avtomatik paydo bo'ladi —
  uni plagindagi `SunatLicense.bas` ga yozasiz.
- **Litsenziyalar:** bloklash / blokdan chiqarish, to'lovsiz litsenziya berish (mijoz + plagin, holat "bo'sh").
- **Yordam videolari:** YouTube havola yoki fayl — saytdagi "Yordam" sahifasida chiqadi.

## Windows dastur
- C# WPF, .NET Framework 4.8, bitta `.exe`; interfeys XAML'siz (Linux'da ham yig'iladi).
- GitHub Actions ("Mini ilova") `SunatPlaginlar.exe` va `SunatPlaginlar-Setup.exe` ni yig'adi.
  `miniilova-v2.0.0` kabi teg qo'yilsa — Releases'ga chiqadi va saytdagi `/dastur/` havolalari ishlaydi.
- Sayt manzili: `https://sunat.cc` (boshqa domen: `AppInfo.DefaultSiteUrl` yoki reyestr
  `HKCU\Software\SunatCC\PlaginlarSozlama\SiteUrl`).

## Kodlar
Bitta algoritm uch joyda: `shop/licensing.py` (sayt), `miniilova/SunatCore` (C#), `SunatLicense.bas` (VBA).
`python tools/testvectors.py` → `miniilova/testvectors.json`; C# testi: `dotnet run --project miniilova/SunatCore.Tests`;
CorelDRAW'da: `Alt+F8` → `SunatTekshiruv`.

**Cheklov:** litsenziya mijoz kompyuterida oflayn tekshiriladi. Qat'iyatli odam buzishi mumkin; kompyuter
almashtirish cheklovlari va tarix oddiy foydalanuvchilarni to'xtatadi.
