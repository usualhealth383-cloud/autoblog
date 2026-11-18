"""나라 × 말 첫 화면(11-18 Main · 곁에 사고: 번역이 script 안 글을 바꿔 문법 오류) — 첫 화면 JS 오류 0 · 응급 단추(전화) 있음 · 번역 뒤 script 안 글이 그대로인지.
쓰는 법: python3 yakjido/tests/ccl.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
C = [(l, t) for l in ('ko-KR', 'en-US', 'es-ES', 'ja-JP', 'zh-CN') for t in ('Asia/Seoul', 'America/New_York', 'Europe/Madrid', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney', 'America/Toronto', 'Pacific/Auckland', 'Africa/Nairobi')]
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    for loc, tz in C:
        c = b.new_context(locale=loc, timezone_id=tz, service_workers='block', viewport={'width': 360, 'height': 780}); pg = c.new_page(); err = []
        pg.on('pageerror', lambda e: err.append(str(e)[:80])); pg.add_init_script(SEED)
        pg.goto(URL + '#/home'); pg.wait_for_timeout(2500)
        pg.evaluate("()=>{const s=document.createElement('script');s.type='text/plain';s.id='zz';s.textContent='응급 119 오늘 약 1577-0199';document.body.appendChild(s);try{if(window.I18N&&I18N.apply)I18N.apply(document.body)}catch(e){}}")
        pg.wait_for_timeout(1200)
        r = pg.evaluate("()=>({sos:!!document.querySelector('.sos-pill,.ink-sos,a[href^=\"tel:\"]'),tel:[...document.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href')).slice(0,2).join(' '),kept:document.getElementById('zz').textContent==='응급 119 오늘 약 1577-0199',cc:window.CC,lang:window.LANG})")
        ok = not err and r['sos'] and r['kept']; bad += not ok
        print(('✓ ' if ok else '✘ ') + f"{loc} {tz} → {r['lang']}/{r['cc']} 응급 {r['sos']} {r['tel']} | script 그대로 {r['kept']} | 오류 {err[:2]}")
        c.close()
    b.close()
srv.shutdown()
print(f'나라 × 말 {len(C)} — 결함 {bad}'); sys.exit(1 if bad else 0)
