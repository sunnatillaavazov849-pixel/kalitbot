@echo off
chcp 65001 >nul
title Tez-Tez bot
cd /d "%~dp0"

python --version >/dev/null 2>nul
if errorlevel 1 (
  echo Python topilmadi. python.org saytidan ornating va "Add python.exe to PATH" belgisini qoying.
  pause
  exit /b 1
)

if not exist venv\Scripts\python.exe (
  echo [1/3] Virtual muhit yaratilmoqda...
  python -m venv venv
  if errorlevel 1 ( pause & exit /b 1 )
)

echo [2/3] Kutubxonalar tekshirilmoqda...
venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo Kutubxonalarni ornatib bolmadi. Internetni tekshiring.
  pause
  exit /b 1
)

if not exist .env (
  copy .env.example .env >nul
  echo.
  echo .env fayli yaratildi va Bloknot ochiladi.
  echo Qiymatlarni toldiring, Ctrl+S bilan saqlang va shu faylni qayta ishga tushiring.
  notepad .env
  pause
  exit /b 0
)

echo [3/3] Bot ishga tushdi. Toxtatish uchun shu oynani yoping.
echo.
venv\Scripts\python bot.py
echo.
echo Bot toxtadi.
pause
