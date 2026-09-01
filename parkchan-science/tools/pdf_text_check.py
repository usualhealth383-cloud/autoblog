#!/usr/bin/env python3
"""인쇄 텍스트 무결성 검사기 — HTML의 모든 보이는 문장이 최종 PDF에 실제로 찍혔는지 대조한다.

배경: 도입부처럼 flex로 짜인 페이지에서 내용이 넘치면 브라우저가 요소를 조용히
압축·클리핑해 문장이 통째로 사라질 수 있다 (2026-09-01 챕터01·02 도입부 리드
둘째 줄 누락 사고). 조판 기하 검사(qa_check)는 화면 레이아웃만 보므로 인쇄
결과의 텍스트 유실은 이 검사가 잡는다.

사용: python3 pdf_text_check.py <chapter.html> <chapter.pdf>
HTML의 텍스트 조각(공백 제거 6자 이상)이 PDF 전체 텍스트에 없으면 exit 1.
"""
import html as htmlmod
import pathlib
import re
import sys

try:
    import pymupdf
except ImportError:  # 구버전 별칭
    import fitz as pymupdf


def html_chunks(path: pathlib.Path):
    t = path.read_text(encoding="utf-8")
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<title.*?</title>", " ", t, flags=re.S)  # 탭 제목은 인쇄되지 않음
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    t = htmlmod.unescape(t)
    out = []
    for line in t.split("\n"):
        norm = re.sub(r"\s+", "", line)
        if len(norm) >= 6:
            out.append((norm, line.strip()[:60]))
    return out


def main():
    src = pathlib.Path(sys.argv[1])
    pdf = pathlib.Path(sys.argv[2])
    doc = pymupdf.open(pdf)
    pdftext = re.sub(r"\s+", "", "".join(p.get_text() for p in doc))
    missing = [(norm, disp) for norm, disp in html_chunks(src) if norm not in pdftext]
    if missing:
        print(f"TEXT FAIL — {pdf.name}: HTML에 있는 문장 {len(missing)}개가 PDF에 없음 (넘침/클리핑 의심)")
        for _, disp in missing[:10]:
            print(f"  ✗ {disp}")
        sys.exit(1)
    print(f"TEXT PASS — {pdf.name}: HTML 문장 전량이 PDF에 인쇄됨")


if __name__ == "__main__":
    main()
