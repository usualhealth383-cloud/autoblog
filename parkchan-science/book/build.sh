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
  curl -sSL -o YeonSung-Regular.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/yeonsung/YeonSung-Regular.ttf"
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

render front-matter/front.html    front-matter/front.pdf
render sample-chapter/chapter.html sample-chapter/chapter.pdf
render chapter-02/chapter.html    chapter-02/chapter.pdf
render chapter-03/chapter.html    chapter-03/chapter.pdf
render chapter-04/chapter.html    chapter-04/chapter.pdf
render mock-exam/exam.html        mock-exam/exam.pdf

# 3) 조판 기하 검증 (위반 시 빌드 실패)
python3 ../tools/qa_check.py front-matter/front.html
python3 ../tools/qa_check.py sample-chapter/chapter.html
python3 ../tools/qa_check.py chapter-02/chapter.html
python3 ../tools/qa_check.py chapter-03/chapter.html
python3 ../tools/qa_check.py chapter-04/chapter.html
python3 ../tools/qa_check.py mock-exam/exam.html --floor-mm 285

# 4) 인쇄 텍스트 무결성 검증 (HTML 문장이 PDF에 전부 찍혔는지 — 클리핑 유실 방지)
python3 -c "import pymupdf" 2>/dev/null || pip install -q pymupdf
python3 ../tools/pdf_text_check.py front-matter/front.html    front-matter/front.pdf
python3 ../tools/pdf_text_check.py sample-chapter/chapter.html sample-chapter/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-02/chapter.html    chapter-02/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-03/chapter.html    chapter-03/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-04/chapter.html    chapter-04/chapter.pdf
python3 ../tools/pdf_text_check.py mock-exam/exam.html        mock-exam/exam.pdf
