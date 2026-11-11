@echo off
title HONAC H-ECU Remote Launcher
color 0B

echo ===================================================
echo   HONAC H-ECU Remote - Setup ^& Launcher
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FOUT] Python is niet gevonden. Installeer Python via python.org en voeg t aan PATH toe.
    pause
    exit
)

echo [1/3] Benodigde bestanden (Flask, waitress & PyAutoGUI) installeren...
python -m pip install flask waitress pyautogui
if %errorlevel% neq 0 (
    echo [FOUT] Installatie mislukt. Check je internetverbinding.
    pause
    exit
)

echo [2/3] Installatie voltooid!
echo.
echo [3/3] Server wordt gestart...
echo.
echo LAAT DIT OPEN STAAN OP DE ACHTERGROND!!
echo.

python app.py
pause