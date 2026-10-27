@echo off
title XAUUSD News Assistant Bot - 24/7 Autonomous Mode
color 0A

echo ========================================================
echo   XAUUSD NEWS ASSISTANT TELEGRAM BOT (CAMBODIA UTC+7)
echo ========================================================
echo.
echo [*] Starting Bot in Autonomous Loop Mode...
echo [*] Features Active:
echo     - 07:00 AM Daily Gold Price Graphic Card (Ultra-HD 1080x1080)
echo     - London 14:00 ^& NY 19:00 Session Open Alerts + Liquidity Heatmap
echo     - 7 Core Pillars Real-Time Breaking News (Zero-Duplicate Shield)
echo     - Interactive Telegram Commands (Sub-Second Response)
echo     - 24/7 Autonomous Self-Healing Operation
echo.

cd /d "%~dp0"

:loop
echo [%date% %time%] Launching bot process...
python -u -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
echo.
echo [!] Bot process stopped or disconnected.
echo [*] Auto-restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
