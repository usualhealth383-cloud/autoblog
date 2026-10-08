#!/usr/bin/env bash
# 본책 챕터 1개 렌더 + 전체 검사 + 그림 검수 시트
# 사용: bash tools/check_chapter.sh 2101   (통합과학1 은 08 · i01 · sample)
set -euo pipefail
cd "$(dirname "$0")/.."
c="$1"
case "$c" in 2*) B=book2/chapter-$c;; sample) B=book/sample-chapter;; *) B=book/chapter-$c;; esac
H="$B/chapter.html"; P="$B/chapter.pdf"
/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$P" "file://$(realpath $H)" 2>/dev/null
echo "OK: $P"
python3 tools/qa_check.py "$H" "$P"
python3 tools/pdf_text_check.py "$H" "$P"
python3 tools/overflow_check.py "$H" | awk '{print} /DEEP>256/{f=1} END{if(f) print "*** 오버플로 있음 ***"}'
python3 tools/fig_zoom.py "$H" "/tmp/figs_$c.png"
