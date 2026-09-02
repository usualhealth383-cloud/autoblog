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
render chapter-05/chapter.html    chapter-05/chapter.pdf
render chapter-06/chapter.html    chapter-06/chapter.pdf
render chapter-07/chapter.html    chapter-07/chapter.pdf
render chapter-08/chapter.html    chapter-08/chapter.pdf
render chapter-09/chapter.html    chapter-09/chapter.pdf
render chapter-10/chapter.html    chapter-10/chapter.pdf
render chapter-11/chapter.html    chapter-11/chapter.pdf
render mock-exam/exam.html        mock-exam/exam.pdf

# 3) 조판 기하 검증 (위반 시 빌드 실패)
python3 ../tools/qa_check.py front-matter/front.html
python3 ../tools/qa_check.py sample-chapter/chapter.html
python3 ../tools/qa_check.py chapter-02/chapter.html
python3 ../tools/qa_check.py chapter-03/chapter.html
python3 ../tools/qa_check.py chapter-04/chapter.html
python3 ../tools/qa_check.py chapter-05/chapter.html
python3 ../tools/qa_check.py chapter-06/chapter.html
python3 ../tools/qa_check.py chapter-07/chapter.html
python3 ../tools/qa_check.py chapter-08/chapter.html
python3 ../tools/qa_check.py chapter-09/chapter.html
python3 ../tools/qa_check.py chapter-10/chapter.html
python3 ../tools/qa_check.py chapter-11/chapter.html
python3 ../tools/qa_check.py mock-exam/exam.html --floor-mm 285

# 4) 인쇄 텍스트 무결성 검증 (HTML 문장이 PDF에 전부 찍혔는지 — 클리핑 유실 방지)
python3 -c "import pymupdf" 2>/dev/null || pip install -q pymupdf
python3 ../tools/pdf_text_check.py front-matter/front.html    front-matter/front.pdf
python3 ../tools/pdf_text_check.py sample-chapter/chapter.html sample-chapter/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-02/chapter.html    chapter-02/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-03/chapter.html    chapter-03/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-04/chapter.html    chapter-04/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-05/chapter.html    chapter-05/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-06/chapter.html    chapter-06/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-07/chapter.html    chapter-07/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-08/chapter.html    chapter-08/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-09/chapter.html    chapter-09/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-10/chapter.html    chapter-10/chapter.pdf
python3 ../tools/pdf_text_check.py chapter-11/chapter.html    chapter-11/chapter.pdf
python3 ../tools/pdf_text_check.py mock-exam/exam.html        mock-exam/exam.pdf

# 5) 합본 PDF (앞부속 + 소단원 01~04 — 현재까지 집필분)
python3 - <<'PYEOF'
import pymupdf
out = pymupdf.open()
for f in ["front-matter/front.pdf", "sample-chapter/chapter.pdf",
          "chapter-02/chapter.pdf", "chapter-03/chapter.pdf", "chapter-04/chapter.pdf",
          "chapter-05/chapter.pdf", "chapter-06/chapter.pdf", "chapter-07/chapter.pdf",
          "chapter-08/chapter.pdf", "chapter-09/chapter.pdf",
          "chapter-10/chapter.pdf", "chapter-11/chapter.pdf"]:
    with pymupdf.open(f) as d:
        out.insert_pdf(d)
try:
    out.subset_fonts()   # 문서별 중복 폰트 정리 (35MB → 14MB)
except Exception:
    pass
out.save("통합과학1_합본.pdf", garbage=4, deflate=True)
print(f"OK: 통합과학1_합본.pdf ({out.page_count}쪽)")
PYEOF
