"""숫자·%·용량이 다르면 오타로 고치지 않는다(11-18 Main · 너스텝 「5% 포도당 → 50%」 사고).
검색어에 숫자가 있으면: ① 고친 검색어(fix·qClean·qSwap)에 같은 숫자가 남아 있어야 하고 ② 1위가 제품이면 제품 이름에 그 숫자가 있어야 한다(없으면 성분·갈래 화면이어야 함 — 다른 숫자 제품이면 결함).
쓰는 법: python3 yakjido/tests/numfix.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys, re, urllib.parse
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
Q = ['타이레놀 500', '타이레놀 650', '타이레놀정 500mg', '타이레놀 8시간', '어린이 타이레놀 80', '어린이타이레놀 160', '이지엔6 프로', '이지엔6 애니', '이지엔6 이브', '이지엔6이브',
     '부루펜 200', '부루펜정 400', '덱시부프로펜 300', '아스피린 100', '아스피린 500', '로라타딘 10mg', '세티리진 10 mg', '판콜에이', '판콜에스', '5% 포도당', '50% 포도당',
     '니코틴 패치 7mg', '니코틴패치 21mg', '마그밀 500', '훼스탈 플러스', '탁센 200', '탁센 이브', '텐텐 츄정', '센트룸 50+', '비타민D 1000', '비타민D 5000IU', '오메가3 1000']
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && D.drugs && D.drugs.length")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    R = pg.evaluate("""L=>L.map(q=>{const h=search(q); const c=window.qClean?qClean(q):q; const r=h[0]||{};
      return {fix:h.fix||'', clean:c, t:r.t||'', h:r.h||''}})""", Q)
    b.close()
srv.shutdown()
num = lambda s: re.findall(r'\d+(?:\.\d+)?', s)
bad = 0
for q, r in zip(Q, R):
    n = num(q); why = []
    for k in ('fix', 'clean'):
        if r[k] and n and sorted(num(r[k])) != sorted(n): why.append(f'{k} 숫자 바뀜: {r[k]}')
    prod = urllib.parse.unquote(r['h'].split('p=')[1]) if 'p=' in r['h'] else (r['t'] if '/brand/' in r['h'] or '/pub' in r['h'] or '/pillinfo' in r['h'] else '')
    pn = num(prod)
    if n and pn and not set(n) & set(pn) and not (set(n) <= {'6'}): why.append(f'다른 숫자 제품: {prod}')
    base = re.sub(r'\d+(\.\d+)?\s*(mg|mcg|ml|iu|g|%|정|알|캡슐|시간|\+)?', ' ', q, flags=re.I).replace(' ', '').replace('어린이', '')
    tm = re.sub(r'\(.*?\)|\s', '', r['t'])
    if n and not pn and not set(n) & set(num(r['t'])) and re.match(r'^/(drug|brand|pub|pillinfo)/', r['h']) and base and tm.startswith(base) and len(tm) > len(base) + 1: why.append(f'숫자 없는 다른 제품: {r["t"]}')   # 「타이레놀 650」 → 타이레놀 콜드처럼
    bad += bool(why)
    print(('✘ ' if why else '✓ ') + q, '→', r['t'][:40], '|', r['h'][:50], '|', '; '.join(why))
print(f'숫자 든 검색 {len(Q)} — 숫자 바꿔 고침·다른 숫자 제품 {bad}')
sys.exit(1 if bad else 0)
