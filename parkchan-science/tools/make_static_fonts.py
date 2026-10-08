#!/usr/bin/env python3
"""교재 조판용 고정 굵기 글꼴 만들기 — 가변 글꼴(NotoSansKR[wght]·NotoSerifKR[wght])에서 400~900 고정 굵기를 뽑는다.

왜: Chromium 은 가변 글꼴을 PDF 에 '쓰는 굵기·크기 조합마다 통째로' 넣는다(소단원 PDF 한 개 9 MB, 합본 140 MB+).
조합이 많아지면 인쇄 자체가 실패한다('Printing failed', 2026-10-02 2104 소단원). 고정 굵기 글꼴은 쓰인 글자만 들어가 작다.
사용: python3 tools/make_static_fonts.py   (이미 있으면 건너뜀) → ~/.fonts/static/NotoSansKR-700.ttf 등
"""
import pathlib, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

SRC = pathlib.Path.home() / '.fonts'
OUT = SRC / 'static'
WEIGHTS = (400, 500, 600, 700, 800, 900)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fam in ('NotoSansKR', 'NotoSerifKR'):
        src = SRC / f'{fam}.ttf'
        if not src.exists(): sys.exit(f'✗ {src} 없음 — build.sh 의 글꼴 내려받기를 먼저')
        for w in WEIGHTS:
            dst = OUT / f'{fam}-{w}.ttf'
            if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime: continue
            f = instancer.instantiateVariableFont(TTFont(src), {'wght': w}, updateFontNames=False)
            f.save(dst); print('OK', dst.name, dst.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
