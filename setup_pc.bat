@echo off
chcp 65001 >nul
title autoblog — 새 PC 로컬 세팅
cd /d "%~dp0"
echo ============================================
echo   autoblog 새 PC 로컬 세팅 (가상환경+패키지+.env)
echo ============================================

echo.
echo [1/3] 가상환경(.venv) 생성
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
) else (
  echo   이미 있음 - 건너뜀
)

echo.
echo [2/3] 패키지 설치 (requirements.txt)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo [3/3] .env 준비
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo   .env 를 새로 만들었습니다.
  echo   ^>^> 메모장으로 .env 를 열어 키를 채우세요. 기존 PC의 .env 내용을 그대로
  echo      복사해 넣는 게 가장 빠릅니다. (.env 는 절대 git 에 올리지 마세요)
) else (
  echo   .env 가 이미 있습니다 - 건너뜀
)

echo.
echo ============== 남은 수동 단계(블로거 로컬 발행 쓸 때만) ==============
echo  1) config\client_secret.json : 기존 PC에서 그대로 복사
echo  2) 블로거_인증.bat 실행      : 이 PC용 token.json 생성(최초 1회 브라우저 동의)
echo.
echo 세팅 완료. 대시보드 실행은  오토블로그_시작.bat  더블클릭.
pause
