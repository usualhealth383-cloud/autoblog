#!/usr/bin/env bash
# 박찬 과학 통합과학2 강의용 교재 빌드 (L-XXXX.html → PDF → 합본)
# 폴리오: 각 챕터 body의 --pg-start 를 순서대로 자동 계산해 연속 번호 부여
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/opt/pw-browsers/chromium}"

# 챕터 순서 (존재하는 파일만)
ORDER=(L-2101 L-2102 L-2103 L-2104 L-2105 L-2201 L-2202 L-2203 L-2204 L-2205 L-2301 L-2302 L-2303)
FILES=()
for c in "${ORDER[@]}"; do [ -f "$c.html" ] && FILES+=("$c"); done

# 외부 CSS의 @font-face는 chromium file:// 에서 로드되지 않으므로 CSS를 인라인 주입한 임시본으로 렌더
render() {
  python3 - "$1" "_tmp_$1" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
html = open(src).read()
css = open('lecture.css').read()
html = html.replace('<link rel="stylesheet" href="lecture.css">', '<style>\n' + css + '\n</style>')
open(dst, 'w').write(html)
PY
  "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$2" "file://$(realpath "_tmp_$1")" 2>/dev/null
  rm -f "_tmp_$1"
  echo "OK: $2"
}

# 1) 폴리오 시작값 계산: 앞 챕터 쪽수 누적 (첫 렌더로 쪽수 파악)
start=0
for c in "${FILES[@]}"; do
  sed -i -E "s/--pg-start:[0-9]+;/--pg-start:${start};/" "$c.html"
  render "$c.html" "$c.pdf"
  n=$(python3 -c "import pymupdf;print(pymupdf.open('$c.pdf').page_count)")
  start=$((start + n))
done

# 2) 텍스트 무결성
for c in "${FILES[@]}"; do python3 ../../tools/pdf_text_check.py "$c.html" "$c.pdf"; done

# 3) 합본
python3 - "${FILES[@]}" <<'PYEOF'
import sys, pymupdf
out = pymupdf.open()
for c in sys.argv[1:]:
    with pymupdf.open(f"{c}.pdf") as d:
        out.insert_pdf(d)
try:
    out.subset_fonts()
except Exception:
    pass
out.save("강의용_통합과학2.pdf", garbage=4, deflate=True)
print(f"OK: 강의용_통합과학2.pdf ({out.page_count}쪽)")
PYEOF
