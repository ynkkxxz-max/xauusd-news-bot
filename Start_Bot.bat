@echo off
title XAUUSD News Assistant Bot - 24/7 Autonomous Mode
color 0A

echo ========================================================
echo   XAUUSD NEWS ASSISTANT TELEGRAM BOT (CAMBODIA UTC+7)
echo ========================================================
echo.
echo [*] Checking 24/7 Cloud Status (Render)...
echo [*] Render Service: https://xauusd-news-bot-1-a6gh.onrender.com
echo.
echo [IMPORTANT NOTICE]:
echo  - If Render Cloud is online, your bot is ALREADY running 24/7!
echo  - This local PC instance will run in PASSIVE STANDBY mode
echo    to strictly PREVENT double-posting into @GoldMarketKH8888.
echo  - You can safely CLOSE this window at any time!
echo ========================================================
echo.

cd /d "%~dp0"

:loop
echo [%date% %time%] Checking Render Cloud health...
curl.exe -s -m 5 https://xauusd-news-bot-1-a6gh.onrender.com/status > nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Render Cloud is ONLINE and actively serving 24/7!
    echo [*] Local instance is in PASSIVE STANDBY mode to prevent double-posting.
    echo [*] You can safely CLOSE this window at any time.
    timeout /t 60 /nobreak >nul
    goto loop
)

echo [!] Render Cloud appears unreachable. Starting Local Fallback Bot...
python -u -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
echo.
echo [!] Bot process stopped or disconnected.
echo [*] Auto-restarting in 10 seconds...
timeout /t 10 /nobreak >nul
goto loop
