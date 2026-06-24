@echo off
chcp 65001 >nul
title 요즘OO 워크스페이스 동기화 (모든 repo clone/pull)
REM 이 스크립트는 autoblog 폴더 안에 있고, 한 단계 위(부모 폴더)에 모든 repo를
REM 나란히 받아 최신화한다. 예) C:\work\autoblog, C:\work\yozm-health ...
cd /d "%~dp0\.."
set OWNER=usualhealth383-cloud

echo ================================================
echo   요즘OO 워크스페이스 동기화
echo   위치: %CD%
echo ================================================

for %%R in (autoblog yozm-health yozm-media auto-trader) do (
  if exist "%%R\.git" (
    echo.
    echo [PULL] %%R
    git -C "%%R" pull --ff-only
  ) else (
    echo.
    echo [CLONE] %%R
    git clone https://github.com/%OWNER%/%%R.git "%%R"
  )
)

echo.
echo ================= 현재 상태(미커밋/미푸시 확인) =================
for %%R in (autoblog yozm-health yozm-media auto-trader) do (
  if exist "%%R\.git" (
    echo.
    echo --- %%R ---
    git -C "%%R" status -sb
  )
)

echo.
echo 완료. 모든 repo가 GitHub 최신과 동기화되었습니다.
echo (PULL 이 실패한 repo가 있으면, 그 repo에 push 안 한 로컬 변경이 있다는 뜻 →
echo  해당 폴더에서 commit 후 push 하세요.)
pause
