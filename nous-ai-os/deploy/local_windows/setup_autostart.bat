@echo off
title NOUS AI OS - Autostart Setup
echo.
echo  Ρύθμιση αυτόματης εκκίνησης NOUS AI OS με τα Windows...
echo.

set NOUS_DIR=%~dp0..\..
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT=%STARTUP_DIR%\NOUS_AI_OS.bat

:: Δημιουργία shortcut στο Startup folder
(
echo @echo off
echo cd /d "%NOUS_DIR%"
echo start /min cmd /c "python -m executor.router"
) > "%SHORTCUT%"

echo  ✅ Έτοιμο!
echo.
echo  Ο NOUS θα ξεκινά αυτόματα κάθε φορά που ανοίγεις τον υπολογιστή.
echo  URL: http://localhost:5000
echo.
echo  Για να αφαιρέσεις την αυτόματη εκκίνηση, διέγραψε:
echo  %SHORTCUT%
echo.
pause
