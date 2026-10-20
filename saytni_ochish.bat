@echo off
chcp 65001 >nul
title Sunat.cc sayti - kompyuterda sinash
cd /d "%~dp0"
rem Saytni o'z kompyuteringizda ochadi: http://localhost:8000
rem Ikki marta bosing. Oyna ochiq turgan paytda sayt ishlaydi.

python --version >nul 2>nul
if errorlevel 1 goto nopython

if exist "venv\Scripts\python.exe" goto havevenv
echo [1/4] Birinchi marta tayyorlanmoqda, 1-3 daqiqa kuting...
python -m venv venv
if errorlevel 1 goto failed
:havevenv

echo [2/4] Kutubxonalar tekshirilmoqda...
"venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto nointernet

if exist ".env" goto haveenv
>".env" echo DEBUG=1
:haveenv

echo [3/4] Baza tayyorlanmoqda...
"venv\Scripts\python.exe" manage.py migrate -v 0
if errorlevel 1 goto failed
"venv\Scripts\python.exe" manage.py demo_malumot

echo.
echo [4/4] Sayt ishga tushdi:  http://localhost:8000
echo        Admin panel:        http://localhost:8000/boshqaruv/
echo        Admin login: admin   parol: admin12345
echo.
echo Brauzer o'zi ochiladi. To'xtatish uchun shu oynani yoping.
echo.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 4; Start-Process 'http://localhost:8000/'"
"venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
pause
exit /b 0

:nopython
echo Python topilmadi.
echo python.org/downloads saytidan Python'ni o'rnating.
echo O'rnatishda pastdagi "Add python.exe to PATH" belgisini ALBATTA qo'ying.
echo Keyin shu faylni qayta ikki marta bosing.
start "" https://www.python.org/downloads/
pause
exit /b 1

:nointernet
echo Kutubxonalarni yuklab bo'lmadi. Internetni tekshiring va qayta urinib ko'ring.
pause
exit /b 1

:failed
echo Xato chiqdi. Shu oynani rasmga olib yuboring.
pause
exit /b 1
