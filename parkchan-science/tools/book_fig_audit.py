#!/usr/bin/env python3
"""본책 그림 글자 점검 — 교재 HTML 을 실제 지면(A4, 96 dpi)으로 그려 보고 SVG 그림마다 글자 크기(pt)·겹침·밖으로 나감을 잰다.

2026-10-07 원장님 결정(본책도 강의용과 같은 '균형'): 그림 글자는 인쇄 **8 pt 이상**, 위·아래 첨자는 6 pt 이상.
(강의용은 600 단위 그림이라 viewBox 13 으로 정했고, 본책은 그림 폭이 제각각이라 인쇄 pt 로 잰다.)
글꼴을 실제와 같게 쓰려고 parkchan-science 를 잠깐 로컬 웹 서버로 띄워 연다(file:// 은 @font-face 를 못 읽는다).

사용: python3 tools/book_fig_audit.py book/chapter-02/chapter.html [...] [--pt 8] [--sub 6] [--json 출력.json]
끝 줄: 'BOOK FIG OK n' 또는 'BOOK FIG FAIL k/n'
그림 번호는 그 파일 안 SVG 순서(1부터) — 장식용 작은 아이콘(글자 없는 SVG)은 세지 않는다.
"""
import asyncio, json, os, sys, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = r"""
([PT, SUB]) => { const PX = 96 / 72, out = [];
 const svgs = [...document.querySelectorAll('svg')].filter(sv => sv.querySelector('text') && [...sv.querySelectorAll('text')].some(t => t.textContent.trim()));
 svgs.forEach((sv, idx) => { const R = sv.getBoundingClientRect(); if (!R.width) return;
  const vis = el => { for (let e = el; e && e !== sv; e = e.parentElement){ const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false; } return true; };
  const ts = [...sv.querySelectorAll('text')].filter(t => t.textContent.trim() && vis(t));
  const small = [], items = [];
  const scale = el => { const m = el.getScreenCTM(); return m ? Math.hypot(m.a, m.b) : 1; };
  for (const t of ts){ const r = t.getBoundingClientRect(); items.push({ s:t.textContent.trim().slice(0, 22), x:r.left, y:r.top, w:r.width, h:r.height });
    const pt = parseFloat(getComputedStyle(t).fontSize) * scale(t) / PX;
    const own = [...t.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && pt > 0.5 && pt < PT - 0.05) small.push([t.textContent.trim().slice(0, 22), +pt.toFixed(1)]);
    for (const sp of t.querySelectorAll('tspan')){ if (!sp.textContent.trim()) continue;
      const p2 = parseFloat(getComputedStyle(sp).fontSize) * scale(t) / PX;
      const sub = sp.hasAttribute('baseline-shift') || sp.hasAttribute('dy') || /baseline-shift|super|sub/.test(sp.getAttribute('style') || '');
      if (p2 > 0.5 && p2 < (sub ? SUB : PT) - 0.05) small.push([sp.textContent.trim().slice(0, 22), +p2.toFixed(1)]); } }
  const ov = []; for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++){ const a = items[i], b = items[j];
    const ix = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), iy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    if (ix > 1 && iy > 2 && ix * iy > 0.12 * Math.min(a.w * a.h, b.w * b.h)) ov.push([a.s, b.s]); }
  const oob = items.filter(a => a.x < R.left - 1 || a.y < R.top - 1 || a.x + a.w > R.right + 1 || a.y + a.h > R.bottom + 1).map(a => a.s);
  const near = (sv.closest('[id]') || {}).id || '', cap = (sv.closest('figure, .fig, .q, .qbox, .item, li, .card') || sv.parentElement).textContent.replace(/\s+/g, ' ').trim().slice(0, 30);
  out.push({ n: idx + 1, near, cap, wmm: +(R.width / 96 * 25.4).toFixed(1), small, ov, oob }); });
 return out; }
"""

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=ROOT)
    s = socketserver.TCPServer(('127.0.0.1', 0), h); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

async def main():
    args = sys.argv[1:]; PT, SUB, oj, files = 8.0, 6.0, None, []
    while args:
        a = args.pop(0)
        if a == '--pt': PT = float(args.pop(0))
        elif a == '--sub': SUB = float(args.pop(0))
        elif a == '--json': oj = args.pop(0)
        else: files.append(a)
    srv = serve(); port = srv.server_address[1]; res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg = await b.new_page(viewport={'width': 794, 'height': 1123})
        await pg.emulate_media(media='print')
        for f in files:
            rel = os.path.relpath(os.path.abspath(f), ROOT)
            await pg.goto(f'http://127.0.0.1:{port}/{rel}'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
            res[rel] = await pg.evaluate(JS, [PT, SUB])
        await b.close()
    srv.shutdown()
    tot = sum(len(v) for v in res.values()); bad = 0
    for f, figs in res.items():
        for g in figs:
            if g['small'] or g['ov'] or g['oob']:
                bad += 1
                print(f"✗ {f} #{g['n']} ({g['near'] or g['cap']} · 폭 {g['wmm']} mm): 작은 글자 {len(g['small'])} {g['small'][:3]} · 겹침 {g['ov'][:2]} · 밖으로 {g['oob'][:2]}")
    if oj: json.dump(res, open(oj, 'w'), ensure_ascii=False, indent=1)
    print(f'BOOK FIG OK {tot}' if not bad else f'BOOK FIG FAIL {bad}/{tot}')
    sys.exit(1 if bad else 0)

asyncio.run(main())
