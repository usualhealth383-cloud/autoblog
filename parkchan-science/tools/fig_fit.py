#!/usr/bin/env python3
"""그림 가장자리에서 잘리는 글자를 막는다 — 원본 HTML(강의용·본책·대단원·모의고사)을 실제로 열어 그림마다
글자 잉크 범위가 viewBox 밖으로 나가면 그만큼(+여유 2) viewBox 를 넓히고, 화면 크기(width·height 속성)도 같은 비율로 맞춘다.

svg 는 기본이 overflow:hidden 이라 viewBox 밖 글자는 앱·인쇄 모두 잘린다(2026-10-13 그림 검수: 왼쪽 위 '(가)' 윗부분 잘림 10여 장).
사용: python3 tools/fig_fit.py [--dry] [파일 ...]   → 고친 그림 수. 고친 뒤 check_chapter.sh·render_one.sh 로 쪽 넘침 확인.
"""
import re, sys, glob, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRY = '--dry' in sys.argv
files = [str(pathlib.Path(a).resolve()) for a in sys.argv[1:] if not a.startswith('--')] or sorted(
    glob.glob(str(ROOT / 'book*/lecture-edition/L-*.html')) + glob.glob(str(ROOT / 'book*/chapter-*/chapter.html')) +
    glob.glob(str(ROOT / 'book*/summary-*/summary.html')) + glob.glob(str(ROOT / 'book*/mock-exam*/exam.html')))

JS = r"""
() => [...document.querySelectorAll('svg')].filter(s => !s.parentElement.closest('svg')).map((svg, i) => {
  const vb = svg.viewBox.baseVal; if (!vb || !vb.width) return null;
  const inv = svg.getScreenCTM && svg.getScreenCTM() ? svg.getScreenCTM().inverse() : null; if (!inv) return null;
  let x0 = vb.x, y0 = vb.y, x1 = vb.x + vb.width, y1 = vb.y + vb.height, need = false;
  for (const t of svg.querySelectorAll('text')){
    if (!t.textContent.trim() || t.closest('defs,marker,symbol')) continue;
    if (getComputedStyle(t).display === 'none' || t.getAttribute('font-size') === '0') continue;
    const r = t.getBoundingClientRect(); if (!r.width) continue;
    const p = (x, y) => { const q = svg.createSVGPoint(); q.x = x; q.y = y; return q.matrixTransform(inv); };
    const a = p(r.left, r.top + r.height * 0.12), b = p(r.right, r.bottom - r.height * 0.16);   // 글꼴 위아래 여백을 뺀 잉크 범위
    if (a.y < y0 - 0.3){ y0 = a.y - 2; need = true; } if (b.y > y1 + 0.3){ y1 = b.y + 2; need = true; }
    if (a.x < x0 - 0.3){ x0 = a.x - 2; need = true; } if (b.x > x1 + 0.3){ x1 = b.x + 2; need = true; }
  }
  return need ? { i, vb:[vb.x, vb.y, vb.width, vb.height], nv:[x0, y0, x1 - x0, y1 - y0].map(v => +v.toFixed(1)) } : null;
}).filter(Boolean)
"""

SVG = re.compile(r'<svg\b[^>]*>', re.S)


def fix_tag(tag, nv, ov):
    g = lambda k: (re.search(r'\b' + k + r'="([^"]*)"', tag) or [None, None])[1]
    w, h = g('width'), g('height')
    new = re.sub(r'\bviewBox="[^"]*"', 'viewBox="%s"' % ' '.join(f'{v:g}' for v in nv), tag)
    try:
        if w and h:
            wf, hf = float(w), float(h); sx = nv[2] / ov[2]; sy = nv[3] / ov[3]
            new = re.sub(r'\bwidth="[^"]*"', f'width="{wf * sx:.1f}"', new, count=1)
            new = re.sub(r'\bheight="[^"]*"', f'height="{hf * sy:.1f}"', new, count=1)
    except ValueError:
        pass
    return new


def main():
    total = 0
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = br.new_page(viewport={'width': 1200, 'height': 900})
        for f in files:
            pg.goto('file://' + str(pathlib.Path(f).resolve()), wait_until='load'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(150)
            res = pg.evaluate(JS)
            if not res: continue
            s = open(f).read()
            # 최상위 svg 순서 = 문서 속 '<svg' 순서(원본에 svg 안 svg 는 없다 — 있으면 건너뜀)
            tags = list(SVG.finditer(s))
            if s.count('<svg') != len(tags): print('건너뜀(형식)', f); continue
            depth, tops = 0, []
            for m in re.finditer(r'<svg\b[^>]*>|</svg>', s):
                if m.group(0).startswith('<svg'):
                    if depth == 0: tops.append(m)
                    depth += 1
                else: depth -= 1
            out = s
            for r in sorted(res, key=lambda r: -r['i']):
                m = tops[r['i']]
                if 'viewBox=' not in m.group(0): continue
                out = out[:m.start()] + fix_tag(m.group(0), r['nv'], r['vb']) + out[m.end():]
                total += 1
            print(pathlib.Path(f).relative_to(ROOT), len(res), [f"{r['i']}:{r['vb']}→{r['nv']}" for r in res][:4])
            if not DRY: open(f, 'w').write(out)
    print('맞춘 그림', total, '(dry)' if DRY else '')


if __name__ == '__main__':
    main()
