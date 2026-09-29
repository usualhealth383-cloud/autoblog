#!/usr/bin/env python3
"""성분 읽기 전수 대조 — 식약처 낱알 자료(일반 5,660 · 전문 19,034)의 성분 칸을 앱의 성분 엔진(ingFind)으로 읽어 본다.

실제 앱을 브라우저로 열어 «앱이 쓰는 그 함수»로 센다(파이썬으로 흉내 내면 앱과 어긋난다).
  · 제품 기준: 성분을 하나도 못 읽은 제품 수
  · 성분 기준: 못 읽은 성분 이름 → 몇 개 제품에 들어 있나 (많은 순)

사용:  python3 yakjido/tools/ing_audit.py [--top 60] [--rx|--otc] [--json 파일]
"""
import argparse, functools, http.server, json, pathlib, socketserver, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT.parent / 'docs' / 'yakjido'
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

JS = """async (files) => {
  await lexLoad?.(true);
  const out = {};
  for (const f of files) {
    const rows = await (await fetch('data/' + f)).json();
    let none = 0, parts = 0, miss = 0; const bad = {};
    for (const p of rows) {
      const comps = String(p.ingr || '').split(/[|,]/).map(s => s.trim()).filter(Boolean);
      if (!comps.length) continue;
      let any = false;
      for (const c of comps) { parts++; if (ingFind(c).length) any = true; else { miss++; bad[c] = (bad[c] || 0) + 1; } }
      if (!any) none++;
    }
    out[f] = { products: rows.length, none, parts, miss, bad: Object.entries(bad).sort((a, b) => b[1] - a[1]) };
  }
  return out;
}"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--top', type=int, default=60)
    ap.add_argument('--rx', action='store_true'); ap.add_argument('--otc', action='store_true'); ap.add_argument('--json')
    a = ap.parse_args()
    files = ['pills-rx.json'] if a.rx else ['pills.json'] if a.otc else ['pills.json', 'pills-rx.json']
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS)); h.log_message = lambda *x: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME); pg = br.new_page()
        pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html#/home'); pg.wait_for_selector('.app'); pg.wait_for_timeout(1500)
        res = pg.evaluate(JS, files); br.close()
    for f, r in res.items():
        print(f"\n■ {f}: 제품 {r['products']:,} · 성분을 하나도 못 읽은 제품 {r['none']:,} · 못 읽은 성분 칸 {r['miss']:,}/{r['parts']:,}")
        for name, n in r['bad'][:a.top]: print(f'  {n:5d}  {name}')
    if a.json: pathlib.Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
