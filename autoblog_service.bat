@echo off
chcp 65001 >nul
title autoblog service
cd /d "%~dp0"
:loop
".venv\Scripts\python.exe" scripts\service.py
echo [%date% %time%] service stopped - restarting in 5s...
timeout /t 5 >nul
goto loop
