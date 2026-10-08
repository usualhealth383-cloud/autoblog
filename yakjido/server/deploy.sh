#!/usr/bin/env bash
# 약지도 워커 배포 (macOS/Linux). 처음 한 번: npm i -g wrangler && wrangler login
set -e; cd "$(dirname "$0")"
echo "[1/3] 공공데이터포털 인증키를 붙여 넣고 Enter (화면에 안 보여도 정상)"; wrangler secret put DATA_GO_KR_KEY
echo "[2/3] 배포"; wrangler deploy
echo "[3/3] 확인 — 워커 주소 뒤에 /wx?lat=37.57&lon=126.98 을 붙여 여세요. \"src\":\"kma\" 와 숫자가 보이면 성공."
