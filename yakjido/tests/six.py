# 닥터나우 대비 여섯(11-27) 시험 — 기능마다 한 묶음. python3 yakjido/tests/six.py [D1 D2 ...]
# 공통: 390·320 넘침 0 · 오류 0 · 빈 값(undefined·NaN) 0 · 세로 가운데(tests/align.mjs) 흠 0
import http.server, socketserver, threading, functools, pathlib, json, sys, subprocess, os
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
D = HERE.parent.parent / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
BASE = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}));"
def seed(me): return BASE + f"localStorage.setItem('yakjido.me.v1',{json.dumps(json.dumps(me))});"
ME6 = {'age': 'senior', 'taking': ['ibuprofen', 'naproxen', 'acetaminophen', 'cls:bp.arb', 'omeprazole', 'supp:calcium'],
       'where': {'ibuprofen': '사랑정형외과', 'naproxen': '튼튼내과', 'cls:bp.arb': '튼튼내과'}}
fails = 0
def ok(c, t):
    global fails
    if not c: fails += 1
    print(('✅ ' if c else '❌ ') + t)
def common(b, name, me, hash_, sel, shot=None):
    for w in (390, 320):
        c = b.new_context(locale='ko-KR', viewport={'width': w, 'height': 844}); c.add_init_script(seed(me))
        p = c.new_page(); err = []; p.on('pageerror', lambda e: err.append(str(e)))
        p.goto(URL + '#' + hash_); p.wait_for_selector(sel, timeout=20000); p.wait_for_timeout(600)
        r = p.evaluate("()=>({sw:document.documentElement.scrollWidth,junk:/undefined|NaN|\\[object|null개/.test(document.getElementById('view').innerText)})")
        ok(r['sw'] <= w and not r['junk'] and not err, f'{name} {w}: 넘침·빈 값·오류 0 ({r["sw"]} {err[:1]})')
        if w == 390 and shot: p.screenshot(path=str(HERE / 'rxread' / shot), full_page=True)
        if w == 390: yield p
        c.close()
def align(name, me, hash_):
    env = dict(os.environ, SEED=seed(me), ONLY_HASH='1')
    out = subprocess.run(['/opt/node22/bin/node', str(HERE / 'align.mjs'), URL, hash_], env=env, capture_output=True, text=True, timeout=180).stdout
    n = int(out.split('세로 정렬 흠 ')[1].split('곳')[0]) if '세로 정렬 흠 ' in out else -1
    ok(n == 0, f'{name}: 세로 가운데 흠 {n}' + ('' if n == 0 else '\n' + out[-600:]))
ONLY = sys.argv[1:]
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    if not ONLY or 'D1' in ONLY:
        for p in common(b, 'D1 지도', ME6, '/map', '.mm-g', 'six-D1.png'):
            r = p.evaluate("()=>({g:[...document.querySelectorAll('.mm-g h2')].map(h=>h.childNodes[1].textContent.trim()),rows:document.querySelectorAll('.mm-row').length,pairs:document.querySelectorAll('.mm-p').length,lines:document.querySelectorAll('.mm-svg path').length,sum:document.querySelector('.mm-sum').innerText})")
            ok(set(r['g']) >= {'사랑정형외과', '튼튼내과', '약국에서 산 약', '영양제'}, f'D1: 받은 곳별 묶음 {r["g"]}')
            ok(r['rows'] == 6, f'D1: 약 6줄 ({r["rows"]})')
            ok(r['pairs'] >= 1 and r['lines'] >= 1 and '약사와 확인' in r['sum'], f'D1: 겹침 {r["pairs"]}짝 · 선 {r["lines"]}개 · 「약사와 확인」')
            p.click('.mm-row[data-i="2"] .mm-pl'); p.fill('#mapin', '하나약국'); p.keyboard.press('Enter'); p.wait_for_timeout(400)
            w = p.evaluate("JSON.parse(localStorage.getItem('yakjido.me.v1')).where")
            ok(w.get('acetaminophen') == '하나약국', f'D1: 받은 곳 고쳐 저장 ({w.get("acetaminophen")})')
        for p in common(b, 'D1 빈 약통', {}, '/map', '.empty'): ok(True, 'D1: 약 없을 때 안내')
        align('D1', ME6, '/map')
    b.close()
print('실패', fails); sys.exit(1 if fails else 0)
