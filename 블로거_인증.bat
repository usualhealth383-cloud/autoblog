@echo off
chcp 65001 >nul
title 블로거 인증 (최초 1회)
cd /d "%~dp0"
echo ============================================
echo   블로거 자동발행 인증을 시작합니다 (최초 1회)
echo   잠시 후 브라우저에 구글 동의 창이 열립니다.
echo   본인 계정으로 '계속/허용' 을 눌러주세요.
echo ============================================
".venv\Scripts\python.exe" scripts\authorize.py
echo.
pause
