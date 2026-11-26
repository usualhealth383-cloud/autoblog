# 약 관련 지원 화면 시험(11-26) — 상태 셋(약 없음 · 약 2가지 · 65세 이상 약 6가지)
# 카드마다 출처 칩·확인일 · 맨 위 「지금 챙기실 만한 것」 고르기 · 약 5가지 이상이면 다제약물 먼저 · 390 넘침 0 · 오류 0
import http.server, socketserver, threading, functools, pathlib, json, sys
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parent.parent.parent / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}));"
CASES = [('약 없음', None, 0, None), ('약 2가지', {'taking': ['acetaminophen', 'omeprazole']}, 2, 'mymed'),
         ('65세 이상 약 6가지', {'age': 'senior', 'taking': ['acetaminophen', 'omeprazole', 'cls:bp.arb', 'cls:bp.diur', 'cls:chol.statin', 'cls:dm.met']}, 4, 'multi')]
fails = 0
def ok(c, t):
    global fails
    if not c: fails += 1
    print(('✅ ' if c else '❌ ') + t)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    for name, me, want, first in CASES:
        for w in (390, 320):
            c = b.new_context(locale='ko-KR', viewport={'width': w, 'height': 844})
            c.add_init_script(SEED + (f"localStorage.setItem('yakjido.me.v1',{json.dumps(json.dumps(me))});" if me else ''))
            p = c.new_page(); err = []; p.on('pageerror', lambda e: err.append(str(e)))
            p.goto(URL + '#/support'); p.wait_for_selector('.sup-c', timeout=20000); p.wait_for_timeout(400)
            r = p.evaluate("""()=>{const C=[...document.querySelectorAll('.sup-c')];return {n:C.length,
              nosrc:C.filter(c=>!c.querySelector('.src-chip')).map(c=>c.id), noday:C.filter(c=>!/확인 2026-\\d\\d-\\d\\d/.test(c.textContent)).map(c=>c.id),
              mine:[...document.querySelectorAll('.sup-jump a')].length, first:(document.querySelector('.sup-c')||{}).id, sw:document.documentElement.scrollWidth,
              junk:/undefined|null|NaN|\\[object/.test(document.getElementById('view').textContent)}}""")
            if w == 390:
                ok(r['n'] == 11 and not r['nosrc'] and not r['noday'], f'{name}: 카드 {r["n"]}개 모두 출처·확인일 {r["nosrc"] or ""}{r["noday"] or ""}')
                ok(r['mine'] == want, f'{name}: 지금 챙길 것 {r["mine"]}가지(기대 {want})')
                if first: ok(r['first'] == 'sup-' + first, f'{name}: 맨 앞 카드 {r["first"]}')
                if name.startswith('65'): p.screenshot(path=str(pathlib.Path(__file__).parent / 'rxread' / 'support-390.png'))
            ok(r['sw'] <= w and not r['junk'] and not err, f'{name}: {w} 넘침 0 · 빈 값 0 · 오류 0 ({r["sw"]}{err[:1]})')
            c.close()
    b.close()
print('실패', fails); sys.exit(1 if fails else 0)
