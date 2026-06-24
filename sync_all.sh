#!/usr/bin/env bash
# 요즘OO 워크스페이스 동기화 (macOS/Linux 용 — Windows 는 sync_all.bat).
# autoblog 폴더 안에 있고, 부모 폴더에 모든 repo 를 나란히 받아 최신화한다.
set -u
cd "$(dirname "$0")/.." || exit 1
OWNER=usualhealth383-cloud
REPOS=(autoblog yozm-health yozm-media auto-trader)

echo "================================================"
echo "  요즘OO 워크스페이스 동기화"
echo "  위치: $(pwd)"
echo "================================================"

for R in "${REPOS[@]}"; do
  if [ -d "$R/.git" ]; then
    echo; echo "[PULL] $R"
    git -C "$R" pull --ff-only
  else
    echo; echo "[CLONE] $R"
    git clone "https://github.com/$OWNER/$R.git" "$R"
  fi
done

echo; echo "============ 현재 상태(미커밋/미푸시 확인) ============"
for R in "${REPOS[@]}"; do
  if [ -d "$R/.git" ]; then
    echo; echo "--- $R ---"
    git -C "$R" status -sb
  fi
done

echo; echo "완료. 모든 repo 가 GitHub 최신과 동기화되었습니다."
