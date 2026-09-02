#!/usr/bin/env bash
# 박찬 과학 통합과학2 조판 빌드 (HTML → PDF, Chromium)
# 폴리오 체계: 앞부속 1~8 예약, I단원 9~ (합본은 챕터 축적분만 우선 병합)
set -euo pipefail
cd "$(dirname "$0")"

# 1) 한글 폰트 (없으면 설치)
if ! fc-list | grep -q "Noto Sans KR"; then
  mkdir -p ~/.fonts && cd ~/.fonts
  curl -sSL -o NotoSansKR.ttf  "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
  curl -sSL -o NotoSerifKR.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifkr/NotoSerifKR%5Bwght%5D.ttf"
  curl -sSL -o NanumPenScript.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumpenscript/NanumPenScript-Regular.ttf"
  curl -sSL -o YeonSung-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/yeonsung/YeonSung-Regular.ttf"
  fc-cache -f ~/.fonts; cd -
fi

# 2) Chromium
CHROME="${CHROME:-/opt/pw-browsers/chromium}"
command -v "$CHROME" >/dev/null || CHROME=$(command -v chromium chromium-browser google-chrome | head -1)

render() {  # render <html> <pdf>
  "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$2" "file://$(realpath "$1")" 2>/dev/null
  echo "OK: $2"
}

render chapter-2101/chapter.html chapter-2101/chapter.pdf

# 3) 조판 QA
python3 ../tools/qa_check.py chapter-2101/chapter.html

# 4) 텍스트 무결성 (HTML 가시 텍스트 vs PDF 텍스트 레이어)
python3 ../tools/pdf_text_check.py chapter-2101/chapter.html chapter-2101/chapter.pdf

# 5) 합본 PDF (지금까지 완성된 챕터 축적분)
python3 - <<'PYEOF'
import pymupdf
out = pymupdf.open()
for f in ["chapter-2101/chapter.pdf"]:
    with pymupdf.open(f) as d:
        out.insert_pdf(d)
try:
    out.subset_fonts()
except Exception:
    pass
out.save("통합과학2_합본.pdf", garbage=4, deflate=True)
print(f"OK: 통합과학2_합본.pdf ({out.page_count}쪽)")
PYEOF
