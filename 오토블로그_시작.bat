@echo off
chcp 65001 >nul
title 오토블로그 승인 대시보드
cd /d "%~dp0"
echo ============================================
echo   오토블로그 승인 대시보드 시작 중...
echo   잠시 후 브라우저에서 http://127.0.0.1:8780 가 열립니다.
echo   (이 검은 창은 켜둔 채로 두세요. 끄면 종료됩니다.)
echo ============================================
".venv\Scripts\python.exe" dashboard\app.py
pause
