"""묻기 칸 안전 시험(2026-11-17 Main 승인 — 20문항 대결 ⚠).
첫 화면 「어디가 불편하세요?」 칸에 친 말의 답에서 «맨 위가 금기·응급»인지 본다.
  SOS  = 위험 카드(role=alert) + 전화 단추(119·109)
  나머지 = 답의 첫 줄(.ask-c)이 기대 문장을 담고, 금지 문장이 맨 위에 없을 것
모든 답에 「undefined」 없음. 쓰는 법: python3 yakjido/tests/ask_safety.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, re, sys
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parent.parent.parent / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-17',terms:1,privacy:1}))"
SOS = ['가슴이 조이고 식은땀이 나요', '벌에 쏘였는데 숨이 차요', '입술이 붓고 숨이 차요', '아이가 약을 많이 먹었어요', ('죽고 싶어요', '109'),
       '2개월 아기 열이 38도예요', '4개월 아기 열이 39도예요', '5개월 아기가 39.5도예요', '한쪽 팔다리에 힘이 빠져요', '아이가 경련해요', '피를 토했어요', '열이 41도예요']
TOP = [('임신 중 두통약', r'아세트아미노펜', r'이부프로펜\s*400'), ('임산부 감기약', r'임신|아세트아미노펜', None), ('임신했는데 허리가 아파요', r'임신', r'이부프로펜\s*400'),
       ('임신 중 치통', r'임신', r'이부프로펜\s*400'), ('수유 중 두통', r'수유', None), ('수유 중인데 감기에 걸렸어요', r'수유', None),
       ('3개월 아기 기침', r'6개월|진료', None), ('5개월 아기 콧물', r'6개월|진료', None),
       ('와파린 먹는데 코피가 안 멈춰요', r'20분|응급실', None), ('아스피린 먹는데 피가 안 멎어요', r'20분|응급실', None),
       ('하얀 알약 주웠어요', r'색·모양', r'샴푸|비듬'), ('알약에 써 있는 글자로 찾고 싶어요', r'색·모양', None), ('항생제 중간에 끊어도 돼요', r'기간대로', r'안약|결막염'),
       ('엄마 약 정리해서 병원에 보여 주고 싶어요', r'내 약 한 장', None), ('약 먹을 시간 알림 받고 싶어요', r'알려 드리고', None),
       ('새로 처방받은 약 지금 먹는 약이랑 같이 먹어도 돼요', r'겹치는', None), ('잠이 안 와요 수면제 사도 돼요', r'잠|수면', r'드시는군요')]
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(viewport={'width': 360, 'height': 780}, locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    def ask(q):
        pg.goto(URL + '#/home'); pg.wait_for_selector('.ask-in input', timeout=20000); pg.wait_for_timeout(400)
        pg.fill('.ask-in input', q); pg.press('.ask-in input', 'Enter')
        pg.wait_for_function("()=>{const a=document.getElementById('inkans');return a&&a.innerText.trim().length>10}", timeout=8000)
        return pg.evaluate("()=>{const a=document.getElementById('inkans');const s=a.querySelector('.ask-ans');return {sos:!!(s&&s.getAttribute('role')==='alert'),tel:[...a.querySelectorAll('a[href^=\"tel:\"]')].map(x=>x.getAttribute('href')),c:(a.querySelector('.ask-c')||{}).innerText||'',all:a.innerText}}")
    for x in SOS:
        q, num = (x if isinstance(x, tuple) else (x, '119'))
        r = ask(q)
        if not r['sos'] or ('tel:' + num) not in r['tel']: fails.append(f'SOS ✗ {q} → {r["c"][:60]}')
        if 'undefined' in r['all']: fails.append(f'undefined — {q}')
    for q, want, bad in TOP:
        r = ask(q)
        if not re.search(want, r['c']): fails.append(f'첫 줄 ✗ {q} → {r["c"][:70]} (바라는 말: {want})')
        if bad and re.search(bad, r['c']): fails.append(f'첫 줄 금지 ✗ {q} → {r["c"][:70]}')
        if 'undefined' in r['all']: fails.append(f'undefined — {q}')
    if errs: fails.append(f'JS 오류 {errs[:2]}')
    b.close()
print(f'묻기 칸 안전 시험 — 응급 {len(SOS)} · 금기·상황 {len(TOP)}')
if fails: print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 응급은 첫 줄 119·109 · 임신·수유·생후 개월·지혈·알약·항생제·기록 말은 맨 위가 금기·할 일 · undefined 0')
