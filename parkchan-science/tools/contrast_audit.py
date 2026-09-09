#!/usr/bin/env python3
"""명암비 점검 — 화면에 실제로 그려진 글자의 대비를 재서 WCAG AA(본문 4.5:1, 큰 글씨 3:1) 미만을 찾는다.
사용: python3 tools/contrast_audit.py   (앱이 http://127.0.0.1:8765 에 떠 있어야 한다)
"""
import asyncio, sys
from playwright.async_api import async_playwright

JS = r"""
() => {
  const lum = (r,g,b) => { const f=v=>{v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4);};
    return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const parse = c => { const m=c.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/); return m? [+m[1],+m[2],+m[3], m[4]===undefined?1:+m[4]] : null; };
  const bgOf = el => { let e=el;
    while (e){ const c=parse(getComputedStyle(e).backgroundColor); if (c && c[3]>0.9) return c; e=e.parentElement; }
    return [255,255,255,1]; };
  const out = [];
  document.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height || el.offsetParent===null) return;
    const own = [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim());
    if (!own) return;
    const cs = getComputedStyle(el); const fg = parse(cs.color); if (!fg || fg[3] < .95) return;
    const bg = bgOf(el);
    const L1 = lum(fg[0],fg[1],fg[2]), L2 = lum(bg[0],bg[1],bg[2]);
    const ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const px = parseFloat(cs.fontSize), w = parseInt(cs.fontWeight)||400;
    const large = px >= 24 || (px >= 18.66 && w >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) out.push({ t: el.textContent.trim().slice(0,22), px: Math.round(px), w,
      ratio: +ratio.toFixed(2), need, cls: (el.className||el.tagName).toString().slice(0,26),
      fg: `rgb(${fg[0]},${fg[1]},${fg[2]})`, bg: `rgb(${bg[0]},${bg[1]},${bg[2]})` });
  });
  const seen = new Set();
  return out.filter(o => { const k=o.cls+o.ratio+o.px; if (seen.has(k)) return false; seen.add(k); return true; });
}
"""

async def sweep(pg, label, bad):
    r = await pg.evaluate(JS)
    if r:
        print(f'{label}:')
        for o in r[:5]: print(f"   {o['ratio']:>4} 글자 {o['fg']:16s} 바탕 {o['bg']:16s} .{o['cls']:20s} “{o['t'][:14]}”")
        bad.append((label, len(r)))
    else:
        print(f'{label}: OK')

async def run(theme):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = await (await b.new_context(viewport={'width':390,'height':844}, color_scheme=theme)).new_page()
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(800)
        bad = []
        print(f'── {"어둡게" if theme=="dark" else "밝게"} ──')
        await sweep(pg, '시작', bad)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(1000)
        await sweep(pg, '오늘', bad)
        for v, n in [('list','교재'),('bank','문제'),('talk','이야기'),('plan','일정'),('me','내 정보')]:
            await pg.click(f'.tab[data-v="{v}"]'); await pg.wait_for_timeout(500); await sweep(pg, n, bad)
        await b.close(); return bad

async def main():
    total = []
    for t in ('light','dark'): total += await run(t)
    n = sum(c for _, c in total)
    print(f'\nAA 미만 {n}건')
    sys.exit(1 if n else 0)
asyncio.run(main())
