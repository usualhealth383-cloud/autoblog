#!/usr/bin/env python3
"""원본 HTML 속 그림 하나를 PNG 로 — 그림을 고친 뒤 눈으로 확인할 때.

사용: python3 tools/fig_one.py <원본.html> <그림 속 글자 일부> [출력.png]
  예) python3 tools/fig_one.py book/lecture-edition/L-1101.html '3:12' /tmp/x.png
그 글자가 든 최상위 <svg> 를 실제 교재 글꼴로 그려 2배 해상도로 찍는다(기본 출력: 같은 폴더 _fig_one.png).
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

src, key = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else str(pathlib.Path(__file__).resolve().parent.parent / 'review' / '_fig_one.png')
with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    pg = br.new_page(viewport={'width': 1200, 'height': 900}, device_scale_factor=2)
    pg.goto('file://' + str(src), wait_until='load'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(200)
    n = pg.evaluate("""(k) => { const s = [...document.querySelectorAll('svg')].filter(x => !x.parentElement.closest('svg') && x.textContent.includes(k));
        s.forEach((x, i) => x.setAttribute('data-fig-one', i)); return s.length; }""", key)
    if not n: print('그 글자가 든 그림이 없음:', key); sys.exit(1)
    pg.locator('[data-fig-one="0"]').screenshot(path=out)
    print(f'{out} (같은 글자 그림 {n}개 중 첫째)')
