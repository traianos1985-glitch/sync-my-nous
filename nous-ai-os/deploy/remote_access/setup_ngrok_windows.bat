@echo off
title NOUS AI OS - Remote Access (ngrok)
color 0B
echo.
echo  ==========================================
echo   NOUS - Απομακρυσμένη Πρόσβαση (ngrok)
echo  ==========================================
echo.

:: Έλεγχος αν το ngrok υπάρχει
where ngrok >nul 2>&1
if errorlevel 1 (
    echo [!] Το ngrok δεν βρέθηκε.
    echo.
    echo Κατέβασε το από: https://ngrok.com/download
    echo 1. Φτιάξε δωρεάν λογαριασμό στο ngrok.com
    echo 2. Κατέβασε το ngrok.exe
    echo 3. Τρέξε: ngrok config add-authtoken YOUR_TOKEN
    echo 4. Ξανατρέξε αυτό το script
    echo.
    start https://ngrok.com/download
    pause
    exit /b 1
)

echo [*] Ο NOUS πρέπει να τρέχει στο background.
echo     Άνοιξε πρώτα: deploy\local_windows\start_nous.bat
echo.
echo [*] Εκκίνηση ngrok tunnel στο port 5000...
echo.
echo ============================================
echo  Μόλις ανοίξει το παράθυρο ngrok:
echo  - Βρες τη γραμμή "Forwarding"
echo  - Αντέγραψε το URL (π.χ. https://abc123.ngrok-free.app)
echo  - Άνοιξε αυτό το URL από το κινητό σου!
echo ============================================
echo.
ngrok http 5000
