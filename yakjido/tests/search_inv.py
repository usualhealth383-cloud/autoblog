"""검색 재고 시험(2026-11-17 Main 「화면에 없어도 검색하면 나와야」).
search_queries.txt 의 말마다 앱의 search() 결과가 1건 이상인지, 처방 성분은 ingFind() 로 계열이 읽히는지 본다.
쓰는 법: python3 yakjido/tests/search_inv.py  (빌드 뒤에)"""
import http.server, socketserver, threading, functools, pathlib, json, sys
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parent
D = R.parent.parent / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-17',terms:1,privacy:1}))"
qs, rx, part = [], [], 0
for l in (R / 'search_queries.txt').read_text(encoding='utf-8').splitlines():
    if l.startswith('#'): part += 1; continue
    if l.strip(): (rx if part >= 3 else qs).append(l.strip())
P = json.load(open(R.parent / 'tools' / 'permits.json', encoding='utf-8'))
full = []
for q in rx:
    c = sorted({i for p in P for i in p[4].split('|') if q in i}, key=len); full.append(c[0] if c else q)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && typeof D!=='undefined' && D.drugs && D.drugs.length")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_timeout(1500)
    pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    zero = pg.evaluate("L=>L.filter(q=>!search(q).length && !(Q_CRISIS.test(q) && qSafe(q)))", qs + rx)   # 위기 문장은 위기 카드(109·1577-0199)가 뜨면 통과
    nocls = pg.evaluate("L=>L.filter(t=>!ingFind(t).length)", full)
    b.close()
print(f'검색 재고 — 일상 {len(qs)} · 처방 성분 {len(rx)}')
if zero or nocls:
    print('✗ 0건:', zero); print('✗ 계열 못 읽음:', nocls); sys.exit(1)
print('✓ 전부 1건 이상 · 처방 성분 계열 전부 읽힘')
