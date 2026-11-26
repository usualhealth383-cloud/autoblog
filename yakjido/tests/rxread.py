# 약봉투·처방전 사진 읽기 시험(11-26 · 공용 사진읽기 부품) — 인쇄 약봉투 사진 3장(3~4가지씩)
# ① 이름 맞춤 수 ② 확인 전에 내 약통 0 ③ 밖으로 나가는 요청 0(같은 서버 GET 만) ④ 390 넘침 0
# python3 yakjido/tests/rxread.py   (처음 한 번 사진을 만들고, 글자 인식에 장마다 20~60초)
import http.server, socketserver, threading, functools, pathlib, json, sys
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
D = HERE.parent.parent / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}))"
# 약봉투 — [이름, 한 번, 하루, 날수]. 정답 = 이름 안에 들어 있어야 할 낱말
BAGS = {
  'bag1': {'병원': '튼튼내과의원', 'rows': [['타이레놀정500밀리그람', '1정', '3', '3'], ['부루펜정200밀리그램', '1정', '3', '3'], ['무코스타정', '1정', '3', '3']], 'ans': ['타이레놀', '부루펜', '무코스타']},
  'bag2': {'병원': '바른가정의학과', 'rows': [['노바스크정5밀리그램', '1정', '1', '30'], ['리피토정10밀리그램', '1정', '1', '30'], ['다이아벡스정500밀리그램', '1정', '2', '30'], ['아스피린프로텍트정100밀리그램', '1정', '1', '30']], 'ans': ['노바스크', '리피토', '다이아벡스', '아스피린']},
  'bag3': {'병원': '사랑정형외과', 'rows': [['록소닌정', '1정', '3', '5'], ['스티렌정', '1정', '3', '5'], ['에페리손정', '1정', '3', '5']], 'ans': ['록소닌', '스티렌', '에페리손']},
}
def bag_html(b):
    tr = ''.join(f'<tr><td>{n}</td><td>{d}</td><td>1일 {f}회</td><td>{dy}일분</td></tr>' for n, d, f, dy in b['rows'])
    return f'''<html><body style="margin:0;background:#fff;font-family:'WenQuanYi Zen Hei',sans-serif;color:#111">
<div style="width:900px;padding:40px"><div style="font-size:40px;font-weight:700">약 봉 투</div>
<div style="font-size:26px;margin:10px 0 24px">환자: 홍길동 · 조제일 2026-11-26 · {b['병원']}</div>
<table style="border-collapse:collapse;font-size:30px;width:100%"><tr><th align=left>약품명</th><th>투약량</th><th>횟수</th><th>일수</th></tr>{tr}</table>
<div style="font-size:26px;margin-top:24px">식후 30분 · 하나약국 02-123-4567</div></div></body></html>'''
fails = 0
def ok(c, t):
    global fails
    if not c: fails += 1
    print(('✅ ' if c else '❌ ') + t)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    sh = br.new_page(viewport={'width': 980, 'height': 700})
    for k, b in BAGS.items():
        f = HERE / 'rxread' / f'{k}.png'
        if not f.exists(): sh.set_content(bag_html(b)); sh.wait_for_timeout(200); sh.locator('div').first.screenshot(path=str(f))
    ctx = br.new_context(locale='ko-KR', viewport={'width': 390, 'height': 844})
    ctx.add_init_script(SEED)
    out = []
    ctx.on('request', lambda r: out.append((r.method, r.url)) if not r.url.startswith(URL) and not r.url.startswith(('data:', 'blob:')) else None)
    p = ctx.new_page(); err = []; p.on('pageerror', lambda e: err.append(str(e)))
    p.goto(URL + '#/photo'); p.wait_for_timeout(1500)
    total = hit = 0
    for k, b in BAGS.items():
        before = p.evaluate("JSON.stringify((JSON.parse(localStorage.getItem('yakjido.me.v1')||'{}').taking)||[])")
        p.evaluate('rxOpen()'); p.wait_for_selector('#pr-sh input[data-pr="img"]:not([capture])', timeout=20000)
        p.set_input_files('#pr-sh input[data-pr="img"]:not([capture])', str(HERE / 'rxread' / f'{k}.png'))
        p.wait_for_selector('#pr-sh .pr-row', timeout=240000)
        ow = p.evaluate("document.documentElement.scrollWidth")
        ok(ow <= 390, f'{k}: 글자 확인 창 390 넘침 0 ({ow})')
        p.click('#pr-sh [data-pr="ok"]'); p.wait_for_selector('.rxr, .empty', timeout=30000)
        names = p.evaluate("[...document.querySelectorAll('.rxr-row:not(.rxr-miss) .rxr-main>b')].map(b=>b.textContent)")
        miss = p.evaluate("document.querySelectorAll('.rxr-miss').length")
        got = [a for a in b['ans'] if any(a in n for n in names)]
        total += len(b['ans']); hit += len(got)
        print(f'   {k}: 맞춘 이름 {len(got)}/{len(b["ans"])} · 화면 후보 {names} · 찾지 못함 {miss}')
        bold = p.evaluate("document.querySelectorAll('.rxr-bits b').length")
        ok(bold > 0, f'{k}: 용량·횟수 숫자 굵게 {bold}곳')
        after = p.evaluate("JSON.stringify((JSON.parse(localStorage.getItem('yakjido.me.v1')||'{}').taking)||[])")
        ok(before == after, f'{k}: 「담기」 누르기 전 내 약통 그대로')
        ow = p.evaluate("document.documentElement.scrollWidth"); ok(ow <= 390, f'{k}: 확인 화면 390 넘침 0 ({ow})')
        if k == 'bag2': p.screenshot(path=str(HERE / 'rxread' / 'shot-confirm.png'), full_page=True)
        if k == 'bag3':
            n = p.evaluate("document.querySelectorAll('.rxr-row.on').length")
            p.click('.rxr-go'); p.wait_for_timeout(800)
            t = json.loads(p.evaluate("JSON.stringify((JSON.parse(localStorage.getItem('yakjido.me.v1')||'{}').taking)||[])"))
            ok(len(t) >= n > 0, f'bag3: 「담기」 뒤 내 약통 {len(t)}가지(체크 {n})')
        p.goto(URL + '#/photo'); p.wait_for_timeout(500)
    print(f'이름 맞춤 합계 {hit}/{total}')
    ok(hit >= total - 2, '이름 맞춤 — 10가지 중 8 이상')
    ok(not out, f'밖으로 나간 요청 0 ({out[:3]})')
    ok(not err, f'화면 오류 0 ({err[:2]})')
    br.close()
print('실패', fails); sys.exit(1 if fails else 0)
