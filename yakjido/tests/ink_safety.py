"""잉크 판 안전 시험(2026-11-17 Main 「확인 없이 안심 문구 없음」).

잉크 판 증상 화면에서
  ① 위험 신호를 확인하기 전(아무것도 안 누름)에는 「이렇게 드세요」 답(.answer · .stabs · .pane)이 보이지 않는다
  ② 「하나도 없어요」를 누르면 답이 보인다
  ③ 응급 신호에 체크하면 119 전화 단추가 보인다
  ④ 옛 판은 그대로 — 「하나도 없어요」 단추가 숨어 있고 답이 처음부터 보인다
쓰는 법: python3 yakjido/tests/ink_safety.py  (빌드 뒤에)
"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).resolve().parent.parent.parent / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(_Q, directory=str(D))
srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}))"
import json
SYMS = [x['id'] for x in json.load(open(D / 'data' / 'core.json', encoding='utf-8'))['symptoms']]   # 11-17 전 증상
VIS = "()=>[...document.querySelectorAll('#view .answer, #view .stabs, #view .pane, #view .ink-conc')].some(e=>e.offsetParent!==null)"
fails, n = [], 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    for ink in ('1', '0'):
        ctx = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', viewport={'width': 390, 'height': 844}, service_workers='block')
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script(SEED + f";localStorage.setItem('yakjido.ink','{ink}')")
        for sid in SYMS:
            pg.goto(URL + '#/symptom/' + sid); pg.reload(); pg.wait_for_timeout(1500)
            if not pg.evaluate("()=>!!document.querySelector('#view .rf')"): continue
            n += 1
            before = pg.evaluate(VIS); btn = pg.evaluate("()=>{const b=document.querySelector('#view .rf-none');return !!(b&&b.offsetParent)}")
            if ink == '1':
                if before: fails.append(f'잉크 {sid}: 위험 신호 확인 전에 답이 보입니다')
                if not btn: fails.append(f'잉크 {sid}: 「하나도 없어요」 단추가 없습니다')
                pg.click('#view .rf-none'); pg.wait_for_timeout(400)
                if not pg.evaluate(VIS): fails.append(f'잉크 {sid}: 「하나도 없어요」를 눌러도 답이 안 보입니다')
                pg.goto(URL + '#/symptom/' + sid); pg.reload(); pg.wait_for_timeout(1500)
                pg.evaluate("()=>{window.RF_OK='';const c=document.querySelector('#view .rf-list input');c.click();}"); pg.wait_for_timeout(400)
                if not pg.evaluate("()=>{const a=document.querySelector('#view .rf-hit.er a[href^=\"tel:\"]');return !!(a&&a.offsetParent)}"): fails.append(f'잉크 {sid}: 응급 신호 체크 뒤 119 단추가 안 보입니다')
                pg.evaluate("()=>{const c=document.querySelector('#view .rf-list input:checked');c&&c.click();}")
            else:
                if not before: fails.append(f'옛 판 {sid}: 답이 처음부터 보여야 합니다')
                if btn: fails.append(f'옛 판 {sid}: 「하나도 없어요」 단추가 보이면 안 됩니다')
        if errs: fails.append(f'{"잉크" if ink == "1" else "옛 판"} JS 오류: {errs[:2]}')
        ctx.close()
    b.close()
print(f'잉크 안전 시험 — 증상 {n}개(두 판)')
if fails:
    print(f'실패 {len(fails)}'); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 확인 전 답 숨김 · 「하나도 없어요」 뒤 답 · 응급 체크 뒤 119 · 옛 판 그대로')
