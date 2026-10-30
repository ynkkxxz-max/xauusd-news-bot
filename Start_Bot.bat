@echo off
title XAUUSD News Assistant Bot - 24/7 Autonomous Mode
color 0A

echo ========================================================
echo   XAUUSD NEWS ASSISTANT TELEGRAM BOT (CAMBODIA UTC+7)
echo ========================================================
echo.
echo [IMPORTANT NOTICE]:
echo  - Render Cloud is ALREADY running your bot 24/7!
echo  - Running a local bot concurrently causes double-posting.
echo  - Do NOT run this local bot while Render Cloud is active.
echo  - You can safely CLOSE this window at any time!
echo ========================================================
echo.

cd /d "%~dp0"

:loop
echo [%date% %time%] Local instance on standby to prevent double-posting.
echo Press any key ONLY if you explicitly want to run local fallback bot...
pause >nul

echo [!] Starting Local Fallback Bot...
python -u -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
echo.
echo [!] Bot process stopped or disconnected.
echo [*] Auto-restarting in 10 seconds...
timeout /t 10 /nobreak >nul
goto loop
