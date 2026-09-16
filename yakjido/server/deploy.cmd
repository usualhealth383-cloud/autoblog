@echo off
chcp 65001 >nul
REM 약지도 워커 배포 (Windows) — 이 파일을 더블클릭하거나 터미널에서 실행
REM 처음 한 번: npm i -g wrangler  그리고  wrangler login
cd /d "%~dp0"
echo.
echo [1/3] 공공데이터포털 인증키를 붙여 넣고 Enter (화면에 안 보여도 정상)
wrangler secret put DATA_GO_KR_KEY
if errorlevel 1 goto fail
echo.
echo [2/3] 배포
wrangler deploy
if errorlevel 1 goto fail
echo.
echo [3/3] 확인 — 브라우저에서 워커 주소 뒤에 /wx?lat=37.57^&lon=126.98 을 붙여 여세요. "src":"kma" 와 숫자가 보이면 성공.
pause
exit /b 0
:fail
echo.
echo 실패했어요. 위 빨간 글을 그대로 복사해서 보내 주세요.
pause
exit /b 1
