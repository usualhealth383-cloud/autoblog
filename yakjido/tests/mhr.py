"""나의건강기록 PDF 불러오기 시험(11-19) — 가짜 투약 이력 PDF(tests/mhr_make.py)로:
 ① 기기 안에서만(PDF 읽는 동안 바깥 주소 요청 0) ② 최근 1년만(400일 전 판콜 빠짐) ③ 약 이름 → 약 사전(타이레놀·노바스크·넥시움·뮤코스타) ④ 못 맞춘 줄은 「확인해 주세요」 ⑤ 지금 먹는 약만 미리 표시(일수가 끝나지 않은 것) ⑥ 담기 뒤 내 약통 ⑦ 암호 파일 → 「암호를 넣어 주세요」 · 틀린 암호 → 「맞지 않아요」 · 맞는 암호 → 목록
쓰는 법: python3 yakjido/tests/mhr_make.py && python3 yakjido/tests/mhr.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright
H = pathlib.Path(__file__).resolve().parent; D = H.parents[1] / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
fails = []; ok = lambda c, m: (print(('  ✓ ' if c else '  ✘ ') + m), None if c else fails.append(m))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    c = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block', viewport={'width': 360, 'height': 780}); pg = c.new_page(); pg.add_init_script(SEED)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); outside = []
    pg.on('request', lambda r: outside.append(r.url) if not r.url.startswith(URL) and not r.url.startswith('data:') and not r.url.startswith('blob:') else None)
    pg.goto(URL + '#/mhr'); pg.wait_for_selector('input[type=file]', state='attached', timeout=30000)
    n0 = len(outside); pg.set_input_files('input[type=file]', str(H / 'q' / '가짜_투약이력.pdf')); pg.wait_for_selector('.mhr-r', timeout=60000)
    rows = pg.evaluate("()=>MHR.rows.map(r=>({n:r.name,d:r.date,days:r.days,ok:r.ok&&r.ok.t,on:r.on}))")
    for r in rows: print('   ', r)
    ok(len(outside) == n0, f'PDF 읽는 동안 바깥 요청 0 ({outside[n0:][:2]})')
    names = ' '.join(r['n'] for r in rows)
    ok('판콜' not in names, '400일 전 약은 빠짐(최근 1년)')
    for k in ['타이레놀', '노바스크', '넥시움', '무코스타']: ok(any(k in r['n'] and r['ok'] for r in rows), f'{k} → 약 사전에 맞춤')
    ok(any('노바스크' in r['n'] and r['ok'] and '2.5' not in r['ok'] for r in rows), '노바스크정 5 mg 은 2.5 mg 제품으로 맞추지 않음')
    ok(any('가나다라' in r['n'] and not r['ok'] for r in rows) and '확인해 주세요' in pg.inner_text('#view'), '못 맞춘 줄은 「확인해 주세요」')
    on = {r['n'][:4]: r['on'] for r in rows}; ok(on.get('타이레놀') and on.get('노바스크') and not on.get('무코스타'), '지금 먹는 약만 미리 표시(7일분 40일 전 약은 표시 안 함)')
    t0 = pg.evaluate("()=>(ME.taking||[]).length"); pg.click('#mhrgo'); pg.wait_for_timeout(1500)
    t1 = pg.evaluate("()=>(ME.taking||[]).length"); ok(t1 - t0 >= 3, f'담기 뒤 내 약통 {t0} → {t1}')
    ok(pg.evaluate("()=>!window.MHR.buf && !window.MHR.rows"), '담은 뒤 파일·목록을 들고 있지 않음')
    pg.goto(URL + '#/mhr'); pg.wait_for_selector('input[type=file]', state='attached'); pg.set_input_files('input[type=file]', str(H / 'q' / '가짜_투약이력_암호1234.pdf'))
    pg.wait_for_selector('#mhrpw', timeout=60000); ok('암호를 넣어 주세요' in pg.inner_text('#view'), '암호 파일 → 「암호를 넣어 주세요」')
    pg.fill('#mhrpw', '0000'); pg.click('#mhrpw ~ button'); pg.wait_for_selector('text=암호가 맞지 않아요', timeout=30000); ok(True, '틀린 암호 → 「맞지 않아요」')
    pg.fill('#mhrpw', '1234'); pg.click('#mhrpw ~ button'); pg.wait_for_selector('.mhr-r', timeout=60000); ok(pg.evaluate("()=>MHR.rows.length") >= 4, '맞는 암호 → 목록')
    ok(not errs, f'JS 오류 0 {errs[:2]}')
    pg.screenshot(path=str(H.parent / '공유' / '사진_장면' / '나의건강기록_360.png'))
    b.close()
srv.shutdown()
print('나의건강기록 불러오기: ' + ('전부 통과' if not fails else f'실패 {len(fails)}')); sys.exit(1 if fails else 0)
