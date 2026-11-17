"""가족 프로필(11-17 Main ①) — 더하기·바꾸기·사람마다 따로·서버 이어 보기는 「나」일 때만·모두 지우기. 1분 안"""
import http.server, socketserver, threading, functools, pathlib, sys, json
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "if(!sessionStorage.getItem('s')){sessionStorage.setItem('s','1');localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-17',terms:1,privacy:1}));localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['acetaminophen']}))}"
bad = []
def ok(c, m):
    print(('  ✓ ' if c else '  ✘ ') + m)
    if not c: bad.append(m)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox']); pg = b.new_page(viewport={'width': 390, 'height': 840}, locale='ko-KR')
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(SEED)
    pg.goto(URL + '#/home'); pg.wait_for_selector('.job-box', timeout=20000)
    ok(pg.locator('.prof-row').count() == 0 and pg.locator('a[href="#/people"]').count() == 1, '한 분일 때 이름 줄 없음 · 가족 길 하나')
    pg.click('a[href="#/people"]'); pg.wait_for_selector('#profName')
    pg.click('button:has-text("어머니")'); pg.wait_for_timeout(200)
    ok(pg.locator('[aria-label="약을 드실 분의 나이"] button.on').inner_text().strip() == '65세 이상', '어머니 → 65세 이상 기본')
    pg.click('button:has-text("더하고 그분 약 담기")'); pg.wait_for_load_state('load'); pg.wait_for_selector('.job-hero, .job-box', timeout=20000)
    st = pg.evaluate("({p: JSON.parse(localStorage.getItem('yakjido.profiles.v1')), me: JSON.parse(localStorage.getItem('yakjido.me.v1')), stash: JSON.parse(localStorage.getItem('yakjido.me.v1@me')||'null'), allow: window.profIsMe()})")
    ok(st['p']['active'] != 'me' and len(st['p']['list']) == 2, '어머니가 지금 사람')
    ok(not (st['me'].get('taking') or []) and st['me'].get('age') == 'senior', '어머니 기록은 비어 있고 65세 이상')
    ok('acetaminophen' in (st['stash'] or {}).get('taking', []), '내 약은 따로 쉬어 둠')
    ok(st['allow'] is False, '서버 이어 보기 꺼짐(나 아님)')
    ok('어머니 님 약을 담아 두세요' in pg.inner_text('.job-hero'), '머리글이 어머니 님')
    ok(pg.locator('.prof-chip').count() == 3 and pg.locator('.prof-note').count() == 1, '이름 줄 · 알림 안내')
    pg.evaluate("ME.taking=['ibuprofen'];saveMe()")
    pg.click('.prof-chip:has-text("나")'); pg.wait_for_load_state('load'); pg.wait_for_selector('.job-box', timeout=20000)
    st = pg.evaluate("({me: JSON.parse(localStorage.getItem('yakjido.me.v1')), keys: Object.keys(localStorage).filter(k=>k.startsWith('yakjido.me.v1@'))})")
    ok(st['me'].get('taking') == ['acetaminophen'], '나로 돌아오면 내 약 그대로')
    ok(len(st['keys']) == 1 and 'ibuprofen' in json.loads(pg.evaluate(f"localStorage.getItem('{st['keys'][0]}')"))['taking'], '어머니 약은 따로 남음')
    ok('내 약 1가지' in pg.inner_text('.job-box'), '홈 머리글 내 약 1가지')
    pg.goto(URL + '#/people'); pg.wait_for_selector('.prof-list')
    ok(pg.locator('.prof-list li').count() == 2, '담아 둔 분 둘')
    ok(not errs, '스크립트 오류 없음 ' + ' | '.join(errs[:2]))
    b.close()
srv.shutdown()
print('가족 프로필:', '흠 ' + str(len(bad)) if bad else '전부 통과')
sys.exit(1 if bad else 0)
