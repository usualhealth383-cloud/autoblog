#!/usr/bin/env bash
# 박찬 과학 통합과학1 강의용 교재 빌드 (L-XXXX.html → PDF → 합본)
# 폴리오: 각 챕터 body의 --pg-start 를 순서대로 자동 계산해 연속 번호 부여
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/opt/pw-browsers/chromium}"

# 챕터 순서 (존재하는 파일만)
ORDER=(L-front L-1101 L-1102 L-1103 L-1104 L-sum1 \
       L-1201 L-1202 L-1203 L-1204 L-1205 L-sum2 \
       L-1301 L-1302 L-1303 L-1304 L-1305 L-1306 L-sum3)
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
out.save("강의용_통합과학1.pdf", garbage=4, deflate=True)
print(f"OK: 강의용_통합과학1.pdf ({out.page_count}쪽)")
PYEOF
