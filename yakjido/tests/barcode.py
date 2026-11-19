"""상자 바코드로 담기(11-18) — 검증 숫자 · 조각 하나만 받기 · 못 찾음 길 · 「이 약이 맞아요」 전에는 담기지 않음. 1분"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}));"
OK_CODE, OK_SEQ = '8800502000100', '201201493'   # 바이오아지니나액 — 심평원 표준코드 2026-08-31
def chk(c12):
    s = sum(int(c12[i]) * (3 if i % 2 else 1) for i in range(12)); return c12 + str((10 - s % 10) % 10)
bad = []
def ok(c, m):
    print(('  ✓ ' if c else '  ✘ ') + m)
    if not c: bad.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 360, 'height': 760}, locale='ko-KR', timezone_id='Asia/Seoul'); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    got = []; pg.on('request', lambda r: got.append(r.url) if '/data/barcode/' in r.url else None)
    pg.add_init_script(SEED)
    pg.goto(URL + '#/barcode'); pg.wait_for_selector('#bcin', timeout=20000)
    r = pg.evaluate(f"""async()=>[await 바코드찾기('{OK_CODE}'), await 바코드찾기('{OK_CODE[:-1] + str((int(OK_CODE[-1]) + 1) % 10)}'), await 바코드찾기('{OK_CODE[:12]}'), await 바코드찾기('{chk('880050299999')}')]""")
    ok(r[0].get('seq') == OK_SEQ and '아르기닌' in r[0].get('name', ''), f"맞는 바코드 → 제품 찾음 ({r[0].get('name')})")
    ok(r[1].get('틀림') and r[2].get('틀림'), '검증 숫자 틀림 · 12자리 → 거절')
    ok(r[3].get('없음') == 1, '목록에 없는 바코드 → 없음')
    ok(len(set(u.split('/')[-1] for u in got)) == 1, f'조각 하나만 받음 — {sorted(set(u.split("/")[-1] for u in got))}')
    pg.fill('#bcin', OK_CODE); pg.click('text=찾기'); pg.wait_for_selector('.bc-card', timeout=5000)
    ok('아르기닌' in pg.inner_text('.bc-card') and not any('pub:' + OK_SEQ == x for x in pg.evaluate('ME.taking||[]')), '찾은 카드가 뜨고 아직 담기지 않음')
    pg.click('text=이 약이 맞아요'); pg.wait_for_timeout(1500)
    ok('pub:' + OK_SEQ in pg.evaluate('ME.taking||[]'), '「이 약이 맞아요」 뒤에 담김')
    pg.goto(URL + '#/barcode'); pg.wait_for_selector('#bcin'); pg.fill('#bcin', chk('880050299999')); pg.click('text=찾기'); pg.wait_for_selector('.bc-card', timeout=5000)
    ok('아직 목록에 없어요' in pg.inner_text('.bc-card') and pg.locator('.bc-card a[href="#/photo"]').count() == 1, '못 찾으면 사진·이름 길')
    UN = pg.evaluate("""async()=>{ await Promise.all([pubIndex(),pubPills(),pubPillsRx()]); const ks=['0502','0509','0511','0513','0517']; for (const k of ks){ const j=await (await fetch('data/barcode/'+k+'.json')).json(); for (const [suf,i] of Object.entries(j.c)){ const seq=j.p[i][0]; if(!(PUB.index||[]).some(p=>p.seq===seq) && !findPill(seq)) return '880'+k+suf; } } return null; }""")
    pg.goto(URL + '#/barcode'); pg.wait_for_selector('#bcin'); pg.fill('#bcin', UN or ''); pg.click('text=찾기'); pg.wait_for_selector('.bc-card a[href^="#/search?q="]', timeout=8000)
    ok(UN and pg.locator('.bc-card a[href^="#/search?q="]').count() == 1 and pg.locator('button:has-text("이 약이 맞아요")').count() == 0, f'약지도 자료와 이어지지 않는 바코드({UN}) → 담기 없이 「이름으로 찾기」')
    ok(not errs, '스크립트 오류 없음 ' + ' | '.join(errs[:2]))
    b.close()
srv.shutdown()
print('바코드:', '흠 ' + str(len(bad)) if bad else '전부 통과')
sys.exit(1 if bad else 0)
