#!/usr/bin/env python3
"""선이 지나가는 그림 이름표에 '배경색 테두리(halo)'를 둘러 읽히게 한다 — 원본(강의용·본책·모의고사)을 고친다.

fig_all_audit.py 가 '선이글자지남' 으로 잡은 글자마다: 글자 아래 배경색을 브라우저에서 읽어
<text … stroke="배경색" stroke-width="3" stroke-linejoin="round" paint-order="stroke"> 를 붙인다(지도·도표의 표준 기법).
원본에서 같은 x·y·글자를 가진 <text> 가 정확히 하나일 때만 고친다(아니면 '못 찾음'으로 남겨 손으로).

사용: python3 tools/fig_halo.py [--dry] [--only 접두어]   (그다음 extract_content·extract_bank → fig_all_audit 로 다시 확인)
"""
import json, re, sys, glob, pathlib
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fig_all_audit as A

ROOT = A.ROOT
DRY = '--dry' in sys.argv
ONLY = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''

JS = r"""
(flag) => {
  const svg = document.querySelector('svg'); const res = [];
  const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim());
  const color = el => { const f = getComputedStyle(el).fill; if (!f || f === 'none') return null;
    const m = f.match(/url\("?#([^")]+)"?\)/); if (m){ const g = svg.querySelector('#' + CSS.escape(m[1])); const st = g && g.querySelector('stop');
      return st ? (st.getAttribute('stop-color') || getComputedStyle(st).stopColor) : '#ffffff'; }
    return f; };
  const inv = svg.getScreenCTM().inverse();
  const shapes = [...svg.querySelectorAll('line,polyline,polygon,path,rect,circle,ellipse')].filter(e => !e.closest('defs,marker,text,clipPath,mask,pattern'));
  for (const t of texts){
    const key = t.textContent.trim().slice(0, 24); if (!flag.includes(key)) continue;
    const b = t.getBoundingClientRect(); const cx = b.left + b.width / 2, cy = b.top + b.height / 2;
    // 이 글자를 지나는 선 — 글자보다 뒤(문서 순서)에 그려지면 테두리로는 못 가린다 → 글자를 맨 위로 옮긴다
    let over = false;
    for (const e of shapes){ const cs = getComputedStyle(e); if (cs.stroke === 'none' || !(parseFloat(cs.strokeWidth) > 0)) continue;
      let L = 0; try { L = e.getTotalLength(); } catch { continue; } if (!(L > 0)) continue;
      const n = Math.min(400, Math.ceil(L)); const m = e.getScreenCTM();
      for (let k = 0; k <= n; k++){ const p = e.getPointAtLength(L * k / n); const q = svg.createSVGPoint(); q.x = p.x; q.y = p.y; const c = q.matrixTransform(m);
        if (c.x > b.left + b.width * 0.2 && c.x < b.right - b.width * 0.2 && c.y > b.top + b.height * 0.32 && c.y < b.bottom - b.height * 0.32){
          if (t.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING) over = true; break; } } }
    const old = t.style.visibility; t.style.visibility = 'hidden';
    let bg = null;
    for (const [x, y] of [[cx, cy], [b.left + 2, cy], [b.right - 2, cy]]){ for (const o of document.elementsFromPoint(x, y)){
        if (o === svg || o.tagName === 'text' || o.closest('text') || !(o instanceof SVGGeometryElement)) continue;
        const cs = getComputedStyle(o); if (cs.fill === 'none' || parseFloat(cs.fillOpacity) < 0.5 || parseFloat(cs.opacity) < 0.5) continue;
        bg = color(o); break; } if (bg) break; }
    t.style.visibility = old;
    const pm = inv.multiply(t.parentNode.getScreenCTM()); const cs = getComputedStyle(t);
    res.push({ text: t.textContent, x: t.getAttribute('x'), y: t.getAttribute('y'), bg: bg || '#ffffff', fill: cs.fill, halo: !!t.getAttribute('stroke'), over,
      mat: [pm.a, pm.b, pm.c, pm.d, pm.e, pm.f].map(v => +v.toFixed(4)),
      attrs: { 'font-size': cs.fontSize.replace('px',''), 'font-weight': cs.fontWeight, fill: cs.fill, 'text-anchor': cs.textAnchor } });
  }
  return res;
}
"""


def rgb2hex(c):
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', c or '')
    return '#%02X%02X%02X' % tuple(int(v) for v in m.groups()) if m else (c or '#FFFFFF')


SOURCES = sorted(glob.glob(str(ROOT / 'book*/lecture-edition/L-*.html')) + glob.glob(str(ROOT / 'book*/chapter-*/chapter.html')) +
                 glob.glob(str(ROOT / 'book*/summary-*/summary.html')) + glob.glob(str(ROOT / 'book*/mock-exam*/exam.html')))


def lum(c):
    m = re.match(r'#?([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$', c.strip()) or re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', c)
    if not m: return 1.0
    v = [int(x, 16) / 255 if len(x) == 2 and not x.isdigit() or c.startswith('#') else int(x) / 255 for x in m.groups()]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def halo_color(fx):
    """글자 아래 배경색 — 글자색과 대비가 모자라면(검은 마커를 집은 경우 등) 글자색 반대 쪽 기본색"""
    bg, fg = rgb2hex(fx['bg']), rgb2hex(fx['fill'])
    if bg.upper() in ('#000000', '#000'): bg = '#FFFFFF' if lum(fg) < 0.4 else '#1E2A2E'   # 검정 = 축·마커를 집은 것 — 배경이 아니다(2026-10-13 '기울기' 글자에 검은 테두리)
    L1, L2 = sorted([lum(bg), lum(fg)], reverse=True)
    if (L1 + 0.05) / (L2 + 0.05) >= 2.2: return bg
    return '#FFFFFF' if lum(fg) < 0.4 else '#1E2A2E'


def patch(fig_id, fx):
    """원본에서 같은 x·y·글자의 <text> 를 모두(강의용·본책에 같은 그림이 있으면 양쪽) 고친다.
    선이 글자 위에 그려지면(over) 글자를 그 그림의 맨 끝(위층)으로 옮기고, 부모 좌표·글꼴 속성을 그대로 실어 간다."""
    code = fig_id.split('-')[1] if fig_id.startswith(('C-', 'Q-')) else ''
    files = [f for f in SOURCES if code and code[:4] in f] or SOURCES
    plain = re.sub(r'\s+', ' ', fx['text']).replace('\u00a0', ' ').strip()
    hal = halo_color(fx); out = []
    for f in files + [f for f in SOURCES if f not in files]:
        s = open(f).read()
        pat = re.compile(r'<text\b(?=[^>]*\bx="' + re.escape(fx['x'] or '') + r'")(?=[^>]*\by="' + re.escape(fx['y'] or '') + r'")([^>]*)>(.*?)</text>', re.S)
        hits = [m for m in pat.finditer(s) if re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2)).replace('&nbsp;', ' ')).strip() == plain]
        if not hits: continue
        new = s
        for m in reversed(hits):
            at = m.group(1)
            if 'stroke=' not in at: at += f' stroke="{hal}" stroke-width="3" stroke-linejoin="round" paint-order="stroke"'
            el = '<text' + at + '>' + m.group(2) + '</text>'
            if fx['over']:
                end = new.find('</svg>', m.end())
                ga = ' '.join(f'{k}="{v}"' for k, v in fx['attrs'].items() if v)
                moved = f'<g transform="matrix({",".join(str(v) for v in fx["mat"])})" {ga}>{el}</g>'
                new = new[:m.start()] + new[m.end():end] + moved + new[end:]
            else:
                new = new[:m.start()] + el + new[m.end():]
        if not DRY: open(f, 'w').write(new)
        out.append(f'{pathlib.Path(f).relative_to(ROOT)}×{len(hits)}' + (' 위로' if fx['over'] else ''))
        if fig_id.startswith(('Q-', 'L-')): break          # 문항·탐구 그림은 원본 한 곳
    return ', '.join(out) or None


def main():
    rep = json.loads((A.OUT / 'audit.json').read_text())
    flagged = {x['id']: sorted({o['a'] for o in x['issues'] if o['k'] == '선이글자지남'}) for x in rep}
    flagged = {k: v for k, v in flagged.items() if v and k.startswith(ONLY)}
    figs = {f['id']: f for f in A.collect() if f['id'] in flagged}
    done, miss = 0, []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = br.new_page(viewport={'width': 680, 'height': 600})
        for fid, keys in flagged.items():
            pg.set_content(A.PAGE % A.fix_font(figs[fid]['svg'])); pg.evaluate('document.fonts.ready')
            for fx in pg.evaluate(JS, keys):
                r = patch(fid, fx)
                if r: done += 1; print('OK ', fid, repr(fx['text'][:20]), fx['bg'], '→', r)
                else: miss.append((fid, fx['text'][:24]))
    for m in miss: print('못 찾음', *m)
    print(f'halo {done} · 못 찾음 {len(miss)}' + (' (dry)' if DRY else ''))


if __name__ == '__main__':
    main()
