@echo off
title XAUUSD News Assistant Bot - 24/7 Autonomous Mode
color 0A

echo ========================================================
echo   XAUUSD NEWS ASSISTANT TELEGRAM BOT (CAMBODIA UTC+7)
echo ========================================================
echo.
echo [*] Starting Bot in Autonomous Loop Mode...
echo [*] Features Active:
echo     - 07:00 AM Daily Gold Price Broadcast & Auto-Pin
echo     - London (14:00) & NY (19:00) Session Open Alerts
echo     - 22:00 PM Daily Market Wrap-Up
echo     - Zero-Delay Breaking News & Market Anomaly Alerts
echo     - 15M TradingView SMC Chart Builder
echo     - Interactive Telegram Commands (/price, /levels, /calendar)
echo     - Automatic Weekly Database Cleanup
echo.

cd /d "C:\Users\TG168\Desktop\xauusd-news-assistant"

:loop
echo [%date% %time%] Launching bot process...
python -u -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
echo.
echo [!] Bot process stopped or disconnected.
echo [*] Auto-restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
