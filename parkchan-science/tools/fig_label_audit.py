#!/usr/bin/env python3
"""그림 이름표 점검 — data/figures/*.svg 를 실제로 그려 보고 글자 크기·겹침·밖으로 나감을 잰다.

2026-10-07 원장님 결정 '균형 — 최소 13': 글자는 그림 좌표(viewBox) 기준 13 이상(위·아래 첨자 tspan 은 10 이상).
책(600 단위 ≈ 159 mm)에서 약 9 pt, 폰 카드(352 px)에서 약 7.5 px — 폰은 '크게 보기'와 같이 쓴다.

사용: python3 tools/fig_label_audit.py [개념id ...] [--min 13] [--json 출력.json]
끝 줄: 'FIG LABEL OK n' 또는 'FIG LABEL FAIL k/n'
"""
import asyncio, json, sys, glob, os
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, 'data', 'figures')
JS = r"""
([MIN, SUBMIN]) => { const svg = document.querySelector('svg'); const vb = svg.viewBox.baseVal; const R = svg.getBoundingClientRect(); const k = R.width / vb.width;
 const scaleOf = el => { const m = el.getScreenCTM(), s = svg.getScreenCTM(); return Math.hypot(m.a, m.b) / Math.hypot(s.a, s.b); };
 const vis = el => { for (let e = el; e && e !== svg; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false; } return true; };
 const box = el => { const r = el.getBoundingClientRect(); return {x:(r.x-R.x)/k+vb.x, y:(r.y-R.y)/k+vb.y, w:r.width/k, h:r.height/k}; };
 const ts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && vis(t));
 const small = [], items = [];
 for (const t of ts) { const fs = parseFloat(getComputedStyle(t).fontSize) * scaleOf(t); const b = box(t); items.push({s: t.textContent.trim().slice(0, 24), ...b});
   if (fs > 0.5 && fs < MIN - 0.05) small.push([t.textContent.trim().slice(0, 24), +fs.toFixed(1)]);
   for (const sp of t.querySelectorAll('tspan')) { if (!sp.textContent.trim()) continue; const f2 = parseFloat(getComputedStyle(sp).fontSize) * scaleOf(t);
     const sub = sp.hasAttribute('baseline-shift') || /baseline-shift|super|sub/.test(sp.getAttribute('style') || '') || sp.hasAttribute('dy');
     if (f2 > 0.5 && f2 < (sub ? SUBMIN : MIN) - 0.05) small.push([sp.textContent.trim().slice(0, 24), +f2.toFixed(1)]); } }
 const ov = []; for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) { const a = items[i], b = items[j];
   const ix = Math.min(a.x+a.w, b.x+b.w) - Math.max(a.x, b.x), iy = Math.min(a.y+a.h, b.y+b.h) - Math.max(a.y, b.y);
   if (ix > 1 && iy > 2 && ix*iy > 0.12 * Math.min(a.w*a.h, b.w*b.h)) ov.push([a.s, b.s]); }
 const out = items.filter(a => a.x < vb.x - 1 || a.y < vb.y - 1 || a.x + a.w > vb.x + vb.width + 1 || a.y + a.h > vb.y + vb.height + 1).map(a => a.s);
 return {small, ov, out, n: items.length}; }
"""

async def main():
    args = sys.argv[1:]; mn = 13.0; out_json = None; ids = []
    while args:
        a = args.pop(0)
        if a == '--min': mn = float(args.pop(0))
        elif a == '--json': out_json = args.pop(0)
        else: ids.append(a)
    files = sorted(glob.glob(FIG + '/*.svg'))
    if ids: files = [f for f in files if any(os.path.basename(f).startswith(i) for i in ids)]
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = await b.new_page(viewport={'width': 800, 'height': 600})
        for f in files:
            await pg.set_content('<html><body style="margin:0"><style>svg{width:600px;height:auto;display:block}</style>' + open(f, encoding='utf-8').read() + '</body></html>')
            res[os.path.basename(f)[:-4]] = await pg.evaluate(JS, [mn, mn * 10 / 13])
        await b.close()
    bad = {k: v for k, v in res.items() if v['small'] or v['ov'] or v['out']}
    for k, v in bad.items():
        print(f"✗ {k}: 작은 글자 {len(v['small'])} {v['small'][:4]} · 겹침 {v['ov'][:3]} · 밖으로 {v['out'][:3]}")
    if out_json: json.dump(res, open(out_json, 'w'), ensure_ascii=False, indent=1)
    print(f"FIG LABEL OK {len(res)}" if not bad else f"FIG LABEL FAIL {len(bad)}/{len(res)}")
    sys.exit(1 if bad else 0)

asyncio.run(main())
