@echo off
title NOUS AI OS
color 0A
echo.
echo  ==========================================
echo   NOUS AI OS - Personal Server (Windows)
echo  ==========================================
echo.

:: Βρες τον φάκελο του script
cd /d "%~dp0..\..\"
echo [*] Φάκελος: %CD%

:: Έλεγχος Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python δεν βρέθηκε!
    echo     Κατέβασε από: https://www.python.org/downloads/
    echo     Σημαντικό: Τσέκαρε "Add Python to PATH" κατά την εγκατάσταση
    pause
    exit /b 1
)

:: Εγκατάσταση dependencies (αν χρειαστεί)
echo [*] Έλεγχος dependencies...
pip install -r requirements.txt -q

:: Δημιουργία φακέλων
if not exist "data" mkdir data
if not exist "apps" mkdir apps
if not exist "forge" mkdir forge

:: Φόρτωση API key
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="OPENROUTER_API_KEY" set OPENROUTER_API_KEY=%%b
    )
)

:: Εκκίνηση
echo.
echo  ==========================================
echo   Ο NOUS ξεκινά...
echo.
echo   Άνοιξε: http://localhost:5000
echo   Από κινητό (ίδιο WiFi): http://YOUR_PC_IP:5000
echo.
echo   Για να σταματήσεις: Ctrl+C
echo  ==========================================
echo.

python -m executor.router
pause
