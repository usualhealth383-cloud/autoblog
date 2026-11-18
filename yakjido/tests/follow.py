"""잘못 이어 받기 시험(11-18 Main · 너스텝 사고) — 묻기에서 앞 질문에 붙일 것(누가 먹나요 말)과 새 질문을 가른다.
쓰는 법: python3 yakjido/tests/follow.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys, json
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
A = '타이레놀이랑 판콜 같이 먹어도 돼요'
C = [(A, '변비약 뭐 먹어요', '새'), (A, '그럼 아이는?', '이어'), (A, '어르신은요?', '이어'), (A, '임신 중이에요', '이어'),
     (A, '근데 머리가 너무 아파요', '새'), (A, '그럼 이부프로펜은요?', '새'), (A, '수면제 한 통을 다 먹었어요', '새·응급'),
     ('부루펜 공복에 먹어도 되나여', '아이가 먹어요', '이어'), ('부루펜 공복에 먹어도 되나여', '그럼 일곱 살 애는?', '이어'), ('기침이 안 떨어져', '아이는 숨이 쌕쌕거려요', '새·응급')]
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>window.__이어 && D.drugs && D.drugs.length")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1000)
    R = pg.evaluate("L=>L.map(([a,g])=>{const x=window.__이어(a,g); return {q:x.q, sos:!!(x.r&&x.r.위험), 결:x.r&&(x.r.결||'')}})", [[a, g] for a, g, _ in C])
    b.close()
srv.shutdown()
bad = 0
for (a, g, want), r in zip(C, R):
    got = '이어' if r['q'] != g else '새'
    ok = got == want.split('·')[0] and (('응급' not in want) or r['sos'])
    bad += not ok
    print(('✓ ' if ok else '✘ ') + f'{a} → {g} | 기대 {want} · 실제 {got}{"·응급" if r["sos"] else ""} | {r["결"][:40]}')
print(f'이어 받기 {len(C)} — 잘못 {bad}')
sys.exit(1 if bad else 0)
