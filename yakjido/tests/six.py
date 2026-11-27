# 닥터나우 대비 여섯(11-27) 시험 — 기능마다 한 묶음. python3 yakjido/tests/six.py [D1 D2 ...]
# 공통: 390·320 넘침 0 · 오류 0 · 빈 값(undefined·NaN) 0 · 세로 가운데(tests/align.mjs) 흠 0
import http.server, socketserver, threading, functools, pathlib, json, sys, subprocess, os
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
D = HERE.parent.parent / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
BASE = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}));"
EXTRA = ['']
def seed(me): return BASE + f"localStorage.setItem('yakjido.me.v1',{json.dumps(json.dumps(me))});" + EXTRA[0]
ME6 = {'age': 'senior', 'taking': ['ibuprofen', 'naproxen', 'acetaminophen', 'cls:bp.arb', 'omeprazole', 'supp:calcium'],
       'where': {'ibuprofen': '사랑정형외과', 'naproxen': '튼튼내과', 'cls:bp.arb': '튼튼내과'}}
fails = 0
def ok(c, t):
    global fails
    if not c: fails += 1
    print(('✅ ' if c else '❌ ') + t)
def common(b, name, me, hash_, sel, shot=None):
    for w in (390, 320):
        c = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', viewport={'width': w, 'height': 844}); c.add_init_script(seed(me))
        p = c.new_page(); err = []; p.on('pageerror', lambda e: err.append(str(e)))
        p.goto(URL + '#' + hash_); p.wait_for_selector(sel, timeout=20000, state='attached'); p.wait_for_timeout(600)
        r = p.evaluate("()=>({sw:document.documentElement.scrollWidth,junk:/undefined|NaN|\\[object|null개/.test(document.getElementById('view').innerText)})")
        ok(r['sw'] <= w and not r['junk'] and not err, f'{name} {w}: 넘침·빈 값·오류 0 ({r["sw"]} {err[:1]})')
        if w == 390 and shot: p.screenshot(path=str(HERE / 'rxread' / shot), full_page=True)
        if w == 390: yield p
        c.close()
def align(name, me, hash_):
    env = dict(os.environ, SEED=seed(me), ONLY_HASH='1')
    out = subprocess.run(['/opt/node22/bin/node', str(HERE / 'align.mjs'), URL, hash_], env=env, capture_output=True, text=True, timeout=180).stdout
    n = int(out.split('세로 정렬 흠 ')[1].split('곳')[0]) if '세로 정렬 흠 ' in out else -1
    ok(n == 0, f'{name}: 세로 가운데 흠 {n}' + ('' if n == 0 else '\n' + out[-600:]))
ONLY = sys.argv[1:]
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    if not ONLY or 'D1' in ONLY:
        for p in common(b, 'D1 지도', ME6, '/map', '.mm-g', 'six-D1.png'):
            r = p.evaluate("()=>({g:[...document.querySelectorAll('.mm-g h2')].map(h=>h.childNodes[1].textContent.trim()),rows:document.querySelectorAll('.mm-row').length,pairs:document.querySelectorAll('.mm-p').length,lines:document.querySelectorAll('.mm-svg path').length,sum:document.querySelector('.mm-sum').innerText})")
            ok(set(r['g']) >= {'사랑정형외과', '튼튼내과', '약국에서 산 약', '영양제'}, f'D1: 받은 곳별 묶음 {r["g"]}')
            ok(r['rows'] == 6, f'D1: 약 6줄 ({r["rows"]})')
            ok(r['pairs'] >= 1 and r['lines'] >= 1 and '약사와 확인' in r['sum'], f'D1: 겹침 {r["pairs"]}짝 · 선 {r["lines"]}개 · 「약사와 확인」')
            p.click('.mm-row[data-i="2"] .mm-pl'); p.fill('#mapin', '하나약국'); p.keyboard.press('Enter'); p.wait_for_timeout(400)
            w = p.evaluate("JSON.parse(localStorage.getItem('yakjido.me.v1')).where")
            ok(w.get('acetaminophen') == '하나약국', f'D1: 받은 곳 고쳐 저장 ({w.get("acetaminophen")})')
        for p in common(b, 'D1 빈 약통', {}, '/map', '.empty'): ok(True, 'D1: 약 없을 때 안내')
        align('D1', ME6, '/map')

    TODAY = __import__('datetime').date.today().isoformat()
    if not ONLY or 'D2' in ONLY:
        for me, h, nm in [({'age': 'adult'}, '/drug/ibuprofen?full=1', 'D2 자세히'), ({'age': 'senior'}, '/drug/ibuprofen', 'D2 간단히')]:
            for p in common(b, nm, me, h, '.wg', 'six-D2.png' if 'full' in h else None):
                r = p.evaluate("()=>({now:document.querySelectorAll('.wg-c.now li').length,later:document.querySelectorAll('.wg-c.later li').length,src:document.querySelectorAll('.wg-src .src-chip').length,rev:/응급의학과 의사 검토/.test(document.body.innerText)})")
                ok(r['now'] >= 3 and r['later'] >= 1 and r['src'] >= 1 and not r['rev'], f'{nm}: 바로 병원 {r["now"]} · 다음 진료 {r["later"]} · 근거 칩 {r["src"]} · 검토 표기 없음')
        align('D2', {'age': 'adult'}, '/drug/ibuprofen?full=1')
    if not ONLY or 'D3' in ONLY:
        me = {'taking': ['acetaminophen', 'cls:bp.arb'], 'sched': {'cls:bp.arb': ['08:00']}, 'taken': {TODAY: ['cls:bp.arb@08:00']}, 'chg': [{'d': TODAY, 'id': 'cls:bp.arb', 'a': 1}]}
        mom = {'age': 'senior', 'taking': ['cls:chol.statin', 'omeprazole'], 'sched': {'cls:chol.statin': ['21:00'], 'omeprazole': ['07:30']}, 'taken': {}, 'chg': [{'d': TODAY, 'id': 'cls:chol.statin', 'a': 1}, {'d': TODAY, 'id': 'rosuvastatin', 'a': 0}]}
        prof = "localStorage.setItem('yakjido.profiles.v1',JSON.stringify({active:'me',list:[{id:'me',name:'나'},{id:'mom',name:'어머니'}]}));" + f"localStorage.setItem('yakjido.me.v1@mom',{json.dumps(json.dumps(mom))});"
        EXTRA[0] = prof
        for p in common(b, 'D3 가족', me, '/people', '.fam-chg', 'six-D3.png'):
            r = p.evaluate("()=>({hero:(document.querySelector('.fam-hero')||{}).innerText||'',chg:document.querySelectorAll('.fam-chg li').length})")
            ok('2명 중 1명' in r['hero'] and r['chg'] >= 3, f'D3: 「{r["hero"].replace(chr(10)," ")}」 · 약 바뀜 {r["chg"]}줄')
        align('D3', me, '/people'); EXTRA[0] = ''
    if not ONLY or 'C3' in ONLY:
        for me, nm, want in [({'age': 'senior', 'kidney': True}, 'C3 해당', 'hit'), ({'age': 'adult'}, 'C3 정보 없음', 'none')]:
            for p in common(b, nm, me, '/drug/ibuprofen?full=1', '.mb, .mb-none', 'six-C3.png' if want == 'hit' else None):
                r = p.evaluate("()=>({li:document.querySelectorAll('.mb li').length,t:(document.querySelector('.mb')||{}).innerText||'',none:!!document.querySelector('.mb-none')})")
                ok((r['li'] >= 1 and '신장' in r['t']) if want == 'hit' else r['none'], f'{nm}: 주의 {r["li"]}줄 · 안내 {r["none"]}')
        for p in common(b, 'C3 간단히', {'age': 'senior', 'kidney': True}, '/drug/ibuprofen', '.mb'): ok(True, 'C3: 간단히 보기에도 띠')
        align('C3', {'age': 'senior', 'kidney': True}, '/drug/ibuprofen?full=1')
    if not ONLY or 'C2' in ONLY:
        me = {'age': 'senior', 'kidney': True, 'taking': ['acetaminophen', 'cls:bp.arb'], 'allergy': [{'ing': 'ibuprofen', 'r': 'hives'}]}
        for p in common(b, 'C2 한 장', me, '/visit?s=fever', '.vt-card', 'six-C2.png'):
            p.click('.vt-chips .chip >> nth=1'); p.wait_for_timeout(300)
            r = p.evaluate("()=>({t:document.querySelector('.vt-card').innerText,go:document.querySelectorAll('.vt-go a').length,tel:!!document.querySelector('a[href=\"tel:119\"]'),app:/닥터나우|굿닥|나만의닥터/.test(document.body.innerText)})")
            ok('2~3일' in r['t'] and '아세트아미노펜' in r['t'] and '두드러기' in r['t'] and '신장' in r['t'], 'C2: 증상·언제부터·내 약·알레르기·지병 한 장')
            ok(r['go'] == 3 and r['tel'] and not r['app'], f'C2: 갈 곳 {r["go"]}(119 포함) · 앱 이름 없음')
            p.click('text=크게 보여 주기'); ok(p.evaluate("document.body.classList.contains('vt-big')"), 'C2: 크게 보기')
        for p in common(b, 'C2 증상 화면', me, '/symptom/fever', '.care'):
            ok(p.evaluate("[...document.querySelectorAll('.care button')].some(x=>/진료 갈 때 보여 줄 한 장/.test(x.textContent))"), 'C2: 증상 화면에서 「진료 갈 때 보여 줄 한 장」')
        align('C2', me, '/visit?s=fever')
    if not ONLY or 'C1' in ONLY:
        rec = {'taking': ['pub:199902738', 'acetaminophen'], 'pub': {'pub:199902738': {'name': '에스로반연고', 'full': '에스로반연고(무피로신)', 'ingr': '무피로신', 'rx': '', 'seq': '199902738'}}}
        for p in common(b, 'C1 걸림', rec, '/news', '.nw-card', 'six-C1.png'):
            r = p.evaluate("()=>({red:!!document.querySelector('.nw-card.red'),src:document.querySelector('.nw-src').innerText})")
            ok(r['red'] and '받음' in r['src'], f'C1: 회수 공지 알림 · 「{r["src"][:30]}」')
        for p in common(b, 'C1 홈', rec, '/home', '.hr2'):
            ok(p.evaluate("/회수 공지/.test(document.querySelector('.hr2').innerText)"), 'C1: 홈 내 약 줄에 회수 공지')
        for p in common(b, 'C1 없음', {'taking': ['acetaminophen']}, '/news', '.nw-card'):
            ok(p.evaluate("!!document.querySelector('.nw-card.ok')&&!document.querySelector('.nw-card.red')"), 'C1: 걸린 것 없으면 없다고만(지어낸 예시 없음)')
        align('C1', rec, '/news')
    b.close()
print('실패', fails); sys.exit(1 if fails else 0)
