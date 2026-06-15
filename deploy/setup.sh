#!/usr/bin/env bash
# 오라클 클라우드(Ubuntu) 서버에서 1회 실행 — 오토블로그 상시 서비스 설치
set -e
cd "$(dirname "$0")/.."   # auto_blog 루트로 이동
ROOT="$(pwd)"
echo "== 1) 시간대 한국으로 설정 =="
sudo timedatectl set-timezone Asia/Seoul

echo "== 2) 파이썬/도구 설치 =="
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip

echo "== 3) 가상환경 + 의존성 =="
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo "== 4) 필수 비밀파일 확인 =="
for f in .env config/client_secret.json config/token.json config/telegram_chats.json; do
  if [ ! -f "$f" ]; then echo "  [경고] $f 가 없습니다 — PC에서 업로드 필요"; fi
done

echo "== 5) systemd 서비스 등록(부팅 시 자동 시작) =="
sudo cp deploy/autoblog.service /etc/systemd/system/autoblog.service
sudo systemctl daemon-reload
sudo systemctl enable autoblog
sudo systemctl restart autoblog
sleep 2
sudo systemctl status autoblog --no-pager || true
echo "== 완료. 로그 보기: journalctl -u autoblog -f =="
