#!/usr/bin/env python3
"""그림 자동 검수 — data/figures/*.svg 를 브라우저에서 그려 글자 상자(bbox)를 재고,
① 글자끼리 겹침 ② 캔버스 밖으로 나감 ③ 8px 미만 글자 를 찾아 보고한다.

사용: python3 tools/fig_audit.py [--fix-report out.json]
"""
import asyncio, json, sys, pathlib
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGS = sorted((ROOT / 'data' / 'figures').glob('*.svg'))

JS = """
() => {
  const svg = document.querySelector('svg'); const vb = svg.viewBox.baseVal; const W = vb.width || svg.width.baseVal.value, H = vb.height || svg.height.baseVal.value;
  const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && !t.closest('defs'));
  const box = t => { const b = t.getBBox(); const m = t.getCTM(); const r = svg.getScreenCTM().inverse();
    // 변환 포함한 사각형(회전은 근사)
    const pts = [[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y]) => { const p = svg.createSVGPoint(); p.x=x; p.y=y; const q = p.matrixTransform(m).matrixTransform(r); return [q.x,q.y]; });
    const xs = pts.map(p=>p[0]), ys = pts.map(p=>p[1]);
    return { x:Math.min(...xs), y:Math.min(...ys), w:Math.max(...xs)-Math.min(...xs), h:Math.max(...ys)-Math.min(...ys) }; };
  const items = texts.map(t => ({ t: t.textContent.trim().slice(0,30), fs: parseFloat(getComputedStyle(t).fontSize), b: box(t) }));
  const out = [];
  items.forEach(i => { const b = i.b; if (b.x < -1 || b.y < -1 || b.x + b.w > W + 1 || b.y + b.h > H + 1) out.push({ kind:'밖', a:i.t }); if (i.fs < 7.5) out.push({ kind:'작음', a:i.t, fs:i.fs }); });
  for (let i=0;i<items.length;i++) for (let j=i+1;j<items.length;j++){ const a=items[i].b, b=items[j].b;
    const ox = Math.min(a.x+a.w, b.x+b.w) - Math.max(a.x, b.x), oy = Math.min(a.y+a.h, b.y+b.h) - Math.max(a.y, b.y);
    if (ox > 2 && oy > 2 && ox*oy > 0.15*Math.min(a.w*a.h, b.w*b.h)) out.push({ kind:'겹침', a:items[i].t, b:items[j].t, area:Math.round(ox*oy) }); }
  return { W, H, n: texts.length, out };
}
"""

async def main():
    report = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = await b.new_page()
        for f in FIGS:
            svg = f.read_text(encoding='utf-8')
            await pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            r = await pg.evaluate(JS)
            if r['out']: report[f.stem] = r['out']
        await b.close()
    tot = sum(len(v) for v in report.values())
    kinds = {}
    for v in report.values():
        for o in v: kinds[o['kind']] = kinds.get(o['kind'], 0) + 1
    print(f'그림 {len(FIGS)}장 · 문제 있는 그림 {len(report)}장 · 지적 {tot}건 {kinds}')
    for k, v in sorted(report.items(), key=lambda kv: -len(kv[1]))[:40]:
        print(f'  {k}: ' + ' | '.join(f"{o['kind']}:{o['a']}" + (f"↔{o['b']}" if 'b' in o else '') for o in v[:4]) + (f' …+{len(v)-4}' if len(v) > 4 else ''))
    if len(sys.argv) > 2 and sys.argv[1] == '--fix-report':
        pathlib.Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
asyncio.run(main())
