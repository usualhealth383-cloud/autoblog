"""11-19 현욱님 — 두드러기 걱정 도우미 시험: 묻기 답(가려 주기·걱정 글) · 응급 신호는 119 카드 · 사진 일기(기기 안 · 밖으로 보내는 요청 0 · 시간 순 · 보여 주기 · 지우기). python3 yakjido/tests/hives.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys, base64
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    ctx = b.new_context(locale='ko-KR', service_workers='block', viewport={'width': 360, 'height': 800}); pg = ctx.new_page(); pg.add_init_script(SEED)
    out = []; pg.on('request', lambda r: out.append(r.url) if not r.url.startswith(URL) and not r.url.startswith('data:') else None)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL + '/?old=1#/home'); pg.wait_for_function("()=>window.__답짓기 && window.vHivesS && D.drugs && D.drugs.length")
    pg.evaluate("()=>ensureCore()"); pg.wait_for_function("()=>(D.tips||[]).some(t=>t.id==='life-hives-worry')", timeout=60000)
    A = lambda q: pg.evaluate("q=>{const a=window.__답짓기(q);return a?(a.위험?'위험 '+a.위험.말:JSON.stringify(a)):''}", q)
    for q in ['갑자기 온몸에 두드러기가 났어요', '두드러기 났는데 에이즈 아닐까요', '두드러기가 옴이나 곰팡이랑 어떻게 달라요']:
        a = A(q)
        if '/hives' not in a or '119' not in a: fails.append(f'묻기 {q} → 사진 일기·119 줄 없음: {a[:80]}')
    for q in ['두드러기 나고 입술이 붓고 숨이 차요', '약 먹고 두드러기에 어지러워요']:
        if not A(q).startswith('위험'): fails.append(f'응급 놓침 {q}')
    s = pg.evaluate("q=>{const r=search(q)[0];return r?r.h:''}", '두드러기 에이즈 걱정돼요')
    if s != '/tips?open=life-hives-worry': fails.append(f'찾기 1위 걱정 글 아님 → {s}')
    pg.evaluate("location.hash='#/hives'"); pg.wait_for_selector('#hv-cam', state='attached')
    for i in range(2):
        pg.set_input_files('#hv-cam', files=[{'name': f'a{i}.png', 'mimeType': 'image/png', 'buffer': PNG}]); pg.wait_for_function(f"()=>document.querySelectorAll('.hv-c').length==={i+1}", timeout=10000); pg.wait_for_timeout(50)
    if '앞 사진에서' not in pg.inner_text('#view'): fails.append('두 번째 사진에 「앞 사진에서 … 뒤」가 없음')
    pg.click('text=진료 때 보여 주기'); pg.wait_for_selector('.hv-show')
    if pg.locator('.hv-show figure').count() != 2: fails.append('보여 주기 사진 수가 2가 아님')
    pg.click('.hv-show >> text=닫기')
    pg.locator('.hv-del').first.click(); pg.click('text=지우기 >> nth=-1') if pg.locator('.dlg button:has-text("지우기")').count() == 0 else pg.click('.dlg button:has-text("지우기")')
    pg.wait_for_function("()=>document.querySelectorAll('.hv-c').length===1", timeout=10000)
    if out: fails.append(f'바깥 요청 {len(out)}개: {out[:3]}')
    if errs: fails.append(f'JS 오류: {errs[:2]}')
    b.close()
srv.shutdown()
print('두드러기 도우미: ' + ('전부 통과' if not fails else f'실패 {len(fails)}')); [print('  ✗', f) for f in fails]
sys.exit(1 if fails else 0)
