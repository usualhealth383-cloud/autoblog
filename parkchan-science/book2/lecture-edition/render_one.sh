#!/usr/bin/env bash
# 강의용 챕터 1개 렌더 + 검사 + 미리보기 PNG
# 사용: bash render_one.sh L-2203     → L-2203.pdf, TEXT/OVERFLOW 검사, _previews/L-2203/pN.png
set -euo pipefail
cd "$(dirname "$0")"
c="$1"
CHROME="${CHROME:-/opt/pw-browsers/chromium}"

python3 - "$c.html" "_tmp_$c.html" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
html = open(src).read()
css = open('lecture.css').read()
open(dst, 'w').write(html.replace('<link rel="stylesheet" href="lecture.css">', '<style>\n' + css + '\n</style>'))
PY
"$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$c.pdf" "file://$(realpath "_tmp_$c.html")" 2>/dev/null
rm -f "_tmp_$c.html"
echo "OK: $c.pdf"

python3 ../../tools/pdf_text_check.py "$c.html" "$c.pdf"
python3 check_overflow.py "$c.html" || true

mkdir -p "_previews/$c"
python3 - "$c" <<'PY'
import sys, pymupdf
c = sys.argv[1]
d = pymupdf.open(f'{c}.pdf')
for i, p in enumerate(d):
    p.get_pixmap(dpi=80).save(f'_previews/{c}/p{i+1}.png')
print(f'{d.page_count}쪽 미리보기 → _previews/{c}/')
PY
