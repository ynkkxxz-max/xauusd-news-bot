@echo off
title XAUUSD News Assistant Auto Bot
chcp 65001 >nul
echo ===================================================
echo 🚀 XAUUSD News Assistant — Auto Alert Bot
echo 🇰🇭 Timezone: UTC+7 (Cambodia)
echo 🤖 Mode: Fully Autonomous (Receive-Only)
echo ===================================================
echo.
cd /d "C:\Users\TG168\Desktop\xauusd-news-assistant"
set PYTHONIOENCODING=utf-8
python -c "from main import XAUUSDNewsAssistantBot; bot = XAUUSDNewsAssistantBot(); bot.start_loop()"
pause
