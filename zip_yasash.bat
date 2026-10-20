@echo off
chcp 65001 >nul
title Plagin ZIP yasash
cd /d "%~dp0"
rem Mijozga beriladigan plagin ZIP'ini yasaydi: plagin + yo'riqnoma (+ Sunat.cc Plaginlar.exe, shu papkada bo'lsa).
rem Ishlatish: .gms faylni shu fayl ustiga sudrab tashlang yoki ikki marta bosing.

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"
"%PY%" --version >nul 2>nul
if errorlevel 1 goto nopython

rem Mini ilova ixtiyoriy: shu papkada bo'lsa ZIP'ga qo'shiladi
set "EXEARG="
if exist "Sunat.cc Plaginlar.exe" set EXEARG=--exe "Sunat.cc Plaginlar.exe"

set "GMS=%~1"
if not "%GMS%"=="" goto havegms
echo Plagin .gms faylini shu oynaga sudrab tashlang va Enter bosing:
set /p "GMS="
:havegms
set "GMS=%GMS:"=%"
if not exist "%GMS%" goto nogms

echo.
echo Plagin fayli: %GMS%
echo.
set "PREFIX="
set /p "PREFIX=Plagin belgisi - botdagi bilan bir xil, masalan TT: "
set "NAME="
set /p "NAME=Plagin nomi, masalan Tez-Tez: "
set "VER="
set /p "VER=Versiya, masalan 2.0 - bo'sh qoldirsa ham bo'ladi: "
set "BOT="
set /p "BOT=Bot havolasi, masalan https://t.me/teztez_sunat_bot - bo'sh qoldirsa ham bo'ladi: "
echo.

"%PY%" tools\zip_yasash.py --prefix "%PREFIX%" --name "%NAME%" --version "%VER%" --bot "%BOT%" --gms "%GMS%" %EXEARG%
if errorlevel 1 goto failed

echo.
echo Tayyor. ZIP shu papkada. Endi botga /plagin_zip %PREFIX% yuboring va ZIP faylni jo'nating.
start "" "%~dp0"
pause
exit /b 0

:nopython
echo Python topilmadi. Avval ishga_tushirish.bat ni bir marta ishga tushiring yoki python.org dan o'rnating.
pause
exit /b 1

:nogms
echo Fayl topilmadi: %GMS%
pause
exit /b 1

:failed
echo.
echo ZIP yasab bo'lmadi. Yuqoridagi xabarni o'qing.
pause
exit /b 1
