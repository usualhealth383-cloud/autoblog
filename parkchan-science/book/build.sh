#!/usr/bin/env bash
# 박찬 과학 교재 조판 빌드 (HTML → PDF, Chromium)
set -euo pipefail
cd "$(dirname "$0")"

# 1) 한글 폰트 (없으면 설치)
if ! fc-list | grep -q "Noto Sans KR"; then
  mkdir -p ~/.fonts && cd ~/.fonts
  curl -sSL -o NotoSansKR.ttf  "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
  curl -sSL -o NotoSerifKR.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifkr/NotoSerifKR%5Bwght%5D.ttf"
  curl -sSL -o NanumPenScript.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumpenscript/NanumPenScript-Regular.ttf"
  fc-cache -f ~/.fonts; cd -
fi

# 2) Chromium (Playwright 번들 우선, 없으면 시스템)
CHROME="${CHROME:-/opt/pw-browsers/chromium}"
command -v "$CHROME" >/dev/null || CHROME=$(command -v chromium chromium-browser google-chrome | head -1)

render() {  # render <html> <pdf>
  "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$2" "file://$(realpath "$1")" 2>/dev/null
  echo "OK: $2"
}

render sample-chapter/chapter.html sample-chapter/chapter.pdf
render mock-exam/exam.html        mock-exam/exam.pdf
