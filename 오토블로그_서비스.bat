@echo off
chcp 65001 >nul
title 오토블로그 서비스 (켜둔 채로 두세요)
cd /d "%~dp0"
echo ============================================
echo   오토블로그 상시 서비스
echo   - 매일 06:00 글 자동 생성 + 텔레그램 알림
echo   - 텔레그램 승인 버튼 수신 대기
echo   (이 창은 켜둔 채로 두세요. 끄면 멈춥니다.)
echo ============================================
:loop
".venv\Scripts\python.exe" scripts\service.py
echo.
echo [%date% %time%] 서비스가 종료됨 - 5초 후 자동 재시작...
timeout /t 5 >nul
goto loop
