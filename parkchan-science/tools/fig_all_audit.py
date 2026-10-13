#!/usr/bin/env python3
"""그림 전수 점검 — 앱에 나가는 그림(개념 140 · 문제 은행 · 탐구)과 본책 개념 쪽 그림을 모두 실제로 그려 기계로 잰다.

① 글자끼리 겹침  ② 그림(viewBox) 밖으로 나간 글자  ③ 정의 없는 참조(url(#…) — 화살표 머리가 사라진다)
④ 방향(orient) 없는 화살표 머리(선이 어느 쪽이든 머리는 오른쪽만 본다)  ⑤ 길이 0 인 화살표 선(머리 방향을 못 정함)
⑥ 선·테두리가 글자를 지나감(표 칸을 넘친 글자, 화살표·곡선이 이름표를 덮음)

사용: python3 tools/fig_all_audit.py [--png 폴더] [--only 접두어]   → 끝 줄 'FIG ALL OK n' 또는 'FIG ALL FAIL k/n'
결과 JSON: <png 폴더>/audit.json (그림마다 id · 출처 · 문맥 · 문제 목록) — 눈 검수(PNG + 문맥)에도 같이 쓴다.
2026-10-13: 정답 검수에서 원본은 맞는데 앱 쪽 그림·표가 빠지거나 뭉개진 것이 나와, 앱에 실리는 그림 전부로 넓혔다.
"""
import json, re, sys, glob, os, pathlib
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _extract_common import defs_map, selfcontain

ROOT = pathlib.Path(__file__).resolve().parent.parent
args = sys.argv[1:]
OUT = pathlib.Path(args[args.index('--png') + 1]) if '--png' in args else ROOT / 'review' / '_figs'
ONLY = args[args.index('--only') + 1] if '--only' in args else ''
OUT.mkdir(parents=True, exist_ok=True)
strip = lambda h: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h or '')).strip()


def collect():
    figs = []
    concepts = json.loads((ROOT / 'data' / 'concepts.json').read_text())
    for c in concepts:
        f = ROOT / 'data' / 'figures' / f"{c['id']}.svg"
        if not f.exists(): continue
        ctx = f"[개념 {c['id']}] {c['lessonName']} · {c['title']}\n" + strip(json.dumps(c.get('body', ''), ensure_ascii=False))[:900] + '\n그림 읽는 법: ' + strip(json.dumps(c.get('howto', ''), ensure_ascii=False))[:300]
        figs.append({'id': f"C-{c['id']}", 'src': f'data/figures/{f.name}', 'svg': f.read_text(), 'ctx': ctx})
    bank = json.loads((ROOT / 'data' / 'bank.json').read_text()); bank = bank if isinstance(bank, list) else bank['items']
    for q in bank:
        if not q.get('figure'): continue
        tb = ' / '.join(' | '.join(map(str, r)) for t in (q.get('table') or []) for r in t)
        ch = ' '.join(f'{"①②③④⑤"[i]} {x}' for i, x in enumerate(q.get('choices') or []))
        ctx = (f"[문항 {q['id']}] 발문: {strip(q['stem'])}\n자료: {strip(q.get('data', ''))} {tb}\n보기: {strip(q.get('source', ''))}\n선지: {strip(ch)}\n"
               f"정답: {q.get('answer')}\n해설: {strip(q.get('explain', ''))}\n바로알기: {strip(q.get('wrong', ''))}")
        figs.append({'id': f"Q-{q['id']}", 'src': 'data/bank.json', 'svg': q['figure'], 'ctx': ctx})
    labs = json.loads((ROOT / 'data' / 'labs.json').read_text()); labs = labs if isinstance(labs, list) else labs['items']
    for i, l in enumerate(labs):
        if not l.get('figure'): continue
        ctx = f"[탐구 {l['lessonId']}] {l['title']}\n자료: {strip(json.dumps(l.get('data', ''), ensure_ascii=False))[:600]}\n과정: {strip(json.dumps(l.get('steps', ''), ensure_ascii=False))[:400]}\n결론: {strip(json.dumps(l.get('conclusion', ''), ensure_ascii=False))[:400]}"
        figs.append({'id': f"L-{l['lessonId']}-{i}", 'src': 'data/labs.json', 'svg': l['figure'], 'ctx': ctx})
    # 본책 개념 쪽 그림(문항·해설·탐구 상자 밖) — 앱에는 안 나가지만 인쇄 교재
    for f in sorted(glob.glob(str(ROOT / 'book*/chapter-*/chapter.html')) + glob.glob(str(ROOT / 'book*/summary-*/summary.html'))):
        src = open(f).read(); defs = defs_map(src); soup = BeautifulSoup(src, 'html.parser'); rel = os.path.relpath(f, ROOT)
        tag = rel.split('/')[1] if rel.startswith('book2/chapter') or rel.startswith('book/') else 'b2' + rel.split('/')[1]   # 1권·2권 대단원 마무리 이름이 겹치지 않게(summary-1 ↔ b2summary-1)
        for n, svg in enumerate(x for x in soup.find_all('svg') if not x.find_parent('svg')):
            if svg.find_parent(class_=['q', 'sol', 'lab', 'quickcheck']) or not svg.find('text'): continue
            fig = svg.find_parent('figure'); cap = fig.find('figcaption') if fig else None
            ps = [p.get_text(' ', strip=True) for p in svg.find_all_previous('p', limit=2)][::-1]
            ctx = f"[본책 {rel} 그림 {n}] {cap.get_text(' ', strip=True) if cap else ''}\n앞 문단: " + ' '.join(ps)[:900]
            figs.append({'id': f"B-{tag}-{n:02d}", 'src': rel, 'svg': selfcontain(str(svg), defs, f'b{n}'), 'ctx': ctx})
    return [x for x in figs if x['id'].startswith(ONLY)]


JS = r"""
() => {
  const svg = document.querySelector('svg'); const out = [];
  const vb = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width ? svg.viewBox.baseVal : { x:0, y:0, width:svg.width.baseVal.value, height:svg.height.baseVal.value };
  const inv = svg.getScreenCTM().inverse();
  const toRoot = (el, x, y) => { const p = svg.createSVGPoint(); p.x = x; p.y = y; return p.matrixTransform(el.getScreenCTM()).matrixTransform(inv); };
  const ids = new Set([...svg.querySelectorAll('[id]')].map(e => e.id));
  const html = svg.outerHTML;
  for (const m of html.matchAll(/url\(#([^)]+)\)|href="#([^"]+)"/g)){ const i = m[1] || m[2]; if (!ids.has(i)) out.push({ k:'참조끊김', a:i }); }
  const markers = {}; svg.querySelectorAll('marker').forEach(m => markers[m.id] = m.getAttribute('orient'));
  const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && !t.closest('defs,marker') && getComputedStyle(t).fontSize !== '0px' && t.getAttribute('font-size') !== '0');
  const box = t => { const b = t.getBBox(); const pts = [[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y]) => toRoot(t, x, y));
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y); return { x:Math.min(...xs), y:Math.min(...ys), w:Math.max(...xs)-Math.min(...xs), h:Math.max(...ys)-Math.min(...ys) }; };
  const T = texts.map(t => ({ t:t.textContent.trim().slice(0, 24), b:box(t), el:t })).filter(i => i.b.w > 0.5);
  const core = b => ({ x:b.x, w:b.w, y:b.y + b.h * 0.24, h:b.h * 0.56 });   // 글자 상자는 글꼴 위아래 여백까지라 두 줄 이름표가 늘 겹쳐 보인다 — 글자 몸통만
  T.forEach(i => { const b = { x:i.b.x, w:i.b.w, y:i.b.y + i.b.h * 0.18, h:i.b.h * 0.7 }; if (b.x < vb.x - 1 || b.y < vb.y - 1 || b.x + b.w > vb.x + vb.width + 1 || b.y + b.h > vb.y + vb.height + 1) out.push({ k:'밖', a:i.t }); });
  for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++){ const a = core(T[i].b), b = core(T[j].b);
    const ox = Math.min(a.x+a.w, b.x+b.w) - Math.max(a.x, b.x), oy = Math.min(a.y+a.h, b.y+b.h) - Math.max(a.y, b.y);
    if (ox > 1.5 && oy > 1 && ox * oy > 0.08 * Math.min(a.w*a.h, b.w*b.h)) out.push({ k:'글자겹침', a:T[i].t, b:T[j].t }); }
  const shapes = [...svg.querySelectorAll('line,polyline,polygon,path,rect,circle,ellipse')].filter(e => !e.closest('defs,marker,text,clipPath,mask,pattern'));
  for (const e of shapes){
    const cs = getComputedStyle(e), sw = parseFloat(cs.strokeWidth) || 0;
    const me = e.getAttribute('marker-end') || e.getAttribute('marker-start') || cs.markerEnd;
    if (me && me !== 'none'){ const id = (me.match(/#([^)"]+)/) || [])[1]; if (id && id in markers && !/auto/.test(markers[id] || '')){
        let L = 0; try { L = e.getTotalLength(); } catch {}
        if (L > 0){ const p = e.getPointAtLength(L), q = e.getPointAtLength(Math.max(0, L - 2)); if (Math.abs(p.y - q.y) > 0.3 || p.x < q.x) out.push({ k:'화살머리방향고정', a:id }); } } }
    if (me && me !== 'none'){ let L = -1; try { L = e.getTotalLength(); } catch {} if (L === 0) out.push({ k:'길이0화살', a:e.tagName }); }
    if (cs.stroke === 'none' || sw <= 0 || cs.strokeOpacity === '0' || cs.visibility === 'hidden') continue;
    let L = 0; try { L = e.getTotalLength(); } catch { continue; }
    if (!(L > 0)) continue;
    const n = Math.min(500, Math.ceil(L / 1.2));
    const P = []; for (let s = 0; s <= n; s++){ const p = e.getPointAtLength(L * s / n); P.push(toRoot(e, p.x, p.y)); }
    const scr = svg.getScreenCTM();
    const shown = p => {   // 그 점에서 이 선이 실제로 보이는가 — 위에 칠해진 도형(구슬·칸 배경)이 덮으면 안 보인다
      const q = svg.createSVGPoint(); q.x = p.x; q.y = p.y; const c = q.matrixTransform(scr);
      const st = document.elementsFromPoint(c.x, c.y); const k = st.indexOf(e); if (k < 0) return false;
      return !st.slice(0, k).some(o => o !== svg && !o.closest('text') && o instanceof SVGGeometryElement && getComputedStyle(o).fill !== 'none' && parseFloat(getComputedStyle(o).fillOpacity) > 0.6 && parseFloat(getComputedStyle(o).opacity) > 0.6); };
    for (const i of T){ const b = i.b, mx = b.w * 0.2, my = b.h * 0.32;
      if (i.el.getAttribute('stroke') && (e.compareDocumentPosition(i.el) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;   // 배경색 테두리를 두른 글자가 선 위에 있으면 읽힌다
      const hits = P.filter(p => p.x > b.x + mx && p.x < b.x + b.w - mx && p.y > b.y + my && p.y < b.y + b.h - my).filter(shown);
      if (hits.length >= 2) out.push({ k:'선이글자지남', a:i.t, b:e.tagName }); }
  }
  const seen = new Set(); return { n:T.length, out: out.filter(o => { const k = JSON.stringify(o); if (seen.has(k)) return false; seen.add(k); return true; }) };
}
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#fff}body{padding:10px;width:660px}
svg{display:block;width:640px;height:auto;max-width:none;font-family:'Noto Sans KR',sans-serif}
</style></head><body>%s</body></html>"""


def fix_font(s):
    return s.replace('PC Serif, PC Sans, serif', 'Noto Serif KR, serif').replace('PC Serif', 'Noto Serif KR').replace('PC Sans', 'Noto Sans KR')


def main():
    figs = collect(); res, bad = [], 0
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = br.new_page(viewport={'width': 680, 'height': 600}, device_scale_factor=1.5)
        for i, f in enumerate(figs):
            pg.set_content(PAGE % fix_font(f['svg']), wait_until='load')
            pg.evaluate('document.fonts.ready')
            try: r = pg.evaluate(JS)
            except Exception as e: r = {'n': 0, 'out': [{'k': '그리기실패', 'a': str(e)[:80]}]}
            png = OUT / f"{f['id']}.png"; pg.locator('svg').first.screenshot(path=str(png))
            res.append({'id': f['id'], 'src': f['src'], 'png': str(png), 'ctx': f['ctx'], 'issues': r['out']})
            if r['out']: bad += 1
    (OUT / 'audit.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    from collections import Counter
    cnt = Counter(o['k'] for x in res for o in x['issues'])
    for x in res:
        if x['issues']: print(x['id'], '·', '; '.join(f"{o['k']}:{o.get('a','')}" + (f"/{o['b']}" if 'b' in o else '') for o in x['issues'][:6]))
    print(dict(cnt))
    print(f'FIG ALL OK {len(res)}' if not bad else f'FIG ALL FAIL {bad}/{len(res)}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
