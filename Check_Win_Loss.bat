@echo off
chcp 65001 >nul
title XAUUSD Signal Win/Loss Community Report
color 0B

cd /d "%~dp0"

echo ========================================================
echo   របាយការណ៍ស្ថិតិជួញដូរ XAUUSD AI SIGNAL (WIN / LOSS)
echo ========================================================
echo.

python check_votes.py

echo.
echo ========================================================
echo ចុចគ្រាប់ចុចណាមួយនៅលើក្តារចុច (Keyboard) ដើម្បីបិទផ្ទាំងនេះ...
pause >nul
