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
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox']); pg = b.new_page(viewport={'width': 390, 'height': 840}, locale='ko-KR')
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(SEED)
    pg.goto(URL + '#/home'); pg.wait_for_selector('.job-box, .th-mine', timeout=20000)
    ok(pg.locator('.prof-row').count() == 0 and pg.locator('a[href="#/people"]').count() <= 1, '한 분일 때 이름 줄 없음 · 가족 길 하나')
    pg.click('.scn-more'); pg.click('.th-sheet a[href="#/people"]'); pg.wait_for_selector('#profName')   # 11-18 정리 — 가족은 「더 ›」 시트 안
    pg.click('button:has-text("어머니")'); pg.wait_for_timeout(200)
    ok(pg.locator('[aria-label="약을 드실 분의 나이"] button.on').inner_text().strip() == '65세 이상', '어머니 → 65세 이상 기본')
    pg.click('button:has-text("더하고 그분 약 담기")'); pg.wait_for_load_state('load'); pg.wait_for_selector('.job-hero, .job-box, .th-mine', timeout=20000)
    st = pg.evaluate("({p: JSON.parse(localStorage.getItem('yakjido.profiles.v1')), me: JSON.parse(localStorage.getItem('yakjido.me.v1')), stash: JSON.parse(localStorage.getItem('yakjido.me.v1@me')||'null'), allow: window.profIsMe()})")
    ok(st['p']['active'] != 'me' and len(st['p']['list']) == 2, '어머니가 지금 사람')
    ok(not (st['me'].get('taking') or []) and st['me'].get('age') == 'senior', '어머니 기록은 비어 있고 65세 이상')
    ok('acetaminophen' in (st['stash'] or {}).get('taking', []), '내 약은 따로 쉬어 둠')
    ok(st['allow'] is False, '서버 이어 보기 꺼짐(나 아님)')
    ok('어머니 약을 담아 두세요' in pg.inner_text('.job-hero').replace('\n', ' '), '머리글이 어머니 님')
    ok(pg.locator('.prof-chip').count() == 3 and pg.locator('.prof-note').count() == 1, '이름 줄 · 알림 안내')
    pg.evaluate("ME.taking=['ibuprofen'];saveMe()")
    pg.click('.prof-chip:has-text("나")'); pg.wait_for_load_state('load'); pg.wait_for_selector('.job-box, .th-mine', timeout=20000)
    st = pg.evaluate("({me: JSON.parse(localStorage.getItem('yakjido.me.v1')), keys: Object.keys(localStorage).filter(k=>k.startsWith('yakjido.me.v1@'))})")
    ok(st['me'].get('taking') == ['acetaminophen'], '나로 돌아오면 내 약 그대로')
    ok(len(st['keys']) == 1 and 'ibuprofen' in json.loads(pg.evaluate(f"localStorage.getItem('{st['keys'][0]}')"))['taking'], '어머니 약은 따로 남음')
    ok('내 약 1가지' in pg.inner_text('.th-mine'), '홈 머리글 내 약 1가지')
    pg.goto(URL + '#/people'); pg.wait_for_selector('.prof-list')
    ok(pg.locator('.prof-list li').count() == 2, '담아 둔 분 둘')

    # 1등 로드맵 1 — 가족 모두의 알림(설치 앱 알람 흉내)
    import re as _re
    cap = _re.search(r'^CAP_MOCK = """(.*?)^"""', open(pathlib.Path(__file__).with_name('run.py')).read(), _re.S | _re.M).group(1)
    pn = b.new_page(viewport={'width': 390, 'height': 840}, locale='ko-KR'); pn.clock.install(time='2026-09-28T10:00:00')
    pn.add_init_script(cap)
    pn.add_init_script("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}));localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['ibuprofen'],sched:{ibuprofen:['08:00','20:00']}}));localStorage.setItem('yakjido.profiles.v1',JSON.stringify({active:'me',list:[{id:'me',name:'나'},{id:'mom1',name:'어머니'}]}));localStorage.setItem('yakjido.me.v1@mom1',JSON.stringify({age:'senior',taking:['acetaminophen'],sched:{acetaminophen:['12:00']}}))")
    pn.goto(URL + '#/schedule'); pn.wait_for_selector('.app', timeout=20000); pn.wait_for_timeout(1800)
    L = pn.evaluate("()=>__LN.pending")
    mom = [x for x in L if x.get('title') == '어머니 약 드실 시간']
    mine = [x for x in L if x.get('title') == '약지도 · 약 드실 시간']
    ok(len(mom) >= 7 and all(str(x['extra']['keys']).startswith('p=mom1;') for x in mom), f'어머니 약 알림이 7일치 걸림 — {len(mom)}')
    ok(len(mine) == 13, f'내 알림은 그대로 13 — {len(mine)}')
    ok(len({x['id'] for x in L}) == len(L), '알림 번호 겹침 없음')
    pn.evaluate("()=>tickFromNote('p=mom1;acetaminophen@12:00','2026-09-28')"); pn.wait_for_timeout(800)
    t = pn.evaluate("()=>({mom: JSON.parse(localStorage.getItem('yakjido.me.v1@mom1')).taken, me: ME.taken})")
    ok('acetaminophen@12:00' in (t['mom'] or {}).get('2026-09-28', []) and 'acetaminophen@12:00' not in str(t['me']), '알림의 먹었어요는 어머니 기록에만')
    L2 = pn.evaluate("()=>__LN.pending")
    ok(not any(x.get('title') == '어머니 약 드실 시간' and x['schedule']['at'].startswith('2026-09-28') for x in L2), '먹은 오늘 회차 알림은 지움')

    pn.goto(URL + '#/home'); pn.wait_for_selector('.job-box, .th-mine', timeout=20000); pn.wait_for_timeout(500)
    ft = pn.inner_text('.fam-today') if pn.locator('.fam-today').count() else ''
    ok('어머니' in ft and '님' not in ft and '오늘 약 다 챙겼어요' in ft, f'오늘 가족 약 — 어머니 다 챙김 표시 ({ft[:40]})')

    # 1등 로드맵 3 — 담자마자 겹침 카드
    pg2 = b.new_page(viewport={'width': 360, 'height': 760}, locale='ko-KR'); pg2.add_init_script(SEED)
    pg2.goto(URL + '#/drugs'); pg2.wait_for_selector('.app', timeout=20000); pg2.wait_for_timeout(1200)
    pg2.evaluate("toggleTaking('pancol-a')"); pg2.wait_for_selector('.after-add', timeout=5000)
    ok('같은 성분이 두 군데' in pg2.inner_text('.after-add'), '판콜에이를 담으면 타이레놀과 같은 성분 카드가 곧바로')
    pg2.click('.aa-x'); ok(pg2.locator('.after-add').count() == 0, '닫기')

    # 로드맵 4 · 6 — 영양제끼리 겹침 · 약 바꾼 날
    pg2.evaluate("ME.taking=[...ME.taking,'supp:zinc'];saveMe();ME.taking=[...ME.taking,'supp:lutein'];saveMe()")
    ok(any('구리' in c[1] for c in pg2.evaluate("ixCards(ixRun([])).map(c=>[c.lv,c.t])")), '루테인 + 아연 → 구리 결핍 카드')
    ok(pg2.evaluate("(ME.chg||[]).filter(c=>c.a===1).map(c=>c.id).join(',')").endswith('supp:zinc,supp:lutein'), '담은 날 적힘')
    pg2.evaluate("(()=>{for(let i=6;i>=0;i-=2){const x=new Date();x.setDate(x.getDate()-i);ME.vitals=(ME.vitals||[]);ME.vitals.push({k:'bp',t:dayKey(x)+' 08:00',s:130+i,d:85,w:'아침'});}saveMe();})()")
    pg2.goto(URL + '#/vitals'); pg2.wait_for_selector('.vz', timeout=10000)
    ok(pg2.locator('.vz-chg').count() >= 1 and '약 바꾼 날' in pg2.inner_text('.vz-chgl'), '그래프에 약 바꾼 날 점선')

    # 11-18 Main — srv.js 가 오기 전: «겹침 없음» 거짓 안심 0 · 이미 걸린 가족 알림은 지우지 않음
    pb = b.new_page(viewport={'width': 360, 'height': 760}, locale='ko-KR', timezone_id='Asia/Seoul')
    pb.route('**/srv.js*', lambda rt: rt.abort())   # srv.js 를 막아 «오기 전»에 머물게
    pb.add_init_script(cap)
    pb.add_init_script(SEED + ";localStorage.setItem('yakjido.me.v1',JSON.stringify({taking:['supp:zinc','supp:lutein','acetaminophen'],sched:{acetaminophen:['09:00']}}));localStorage.setItem('yakjido.profiles.v1',JSON.stringify({active:'me',list:[{id:'me',name:'나'},{id:'mom1',name:'어머니'}]}));localStorage.setItem('yakjido.me.v1@mom1',JSON.stringify({taking:['ibuprofen'],sched:{ibuprofen:['12:00']}}))")
    nope = []
    for h in ('#/home', '#/bag', '#/together', '#/check'):
        pb.goto(URL + h, wait_until='commit'); pb.wait_for_timeout(2500)
        t = pb.inner_text('body')
        if '겹침 없음' in t or '조합이 안 보여요' in t or '겹치는 것이 없' in t: nope.append(h)
    ok(not nope, f'srv.js 전 «겹침 없음» 0 — {nope}')
    pb.evaluate("()=>{ __LN.pending.push({id:100005,title:'어머니 약 드실 시간',schedule:{at:new Date(Date.now()+3600e3).toISOString()},extra:{}}); }")
    pb.evaluate("()=>window.nativeArm && nativeArm()"); pb.wait_for_timeout(800)
    ok(pb.evaluate("()=>__LN.pending.some(x=>x.id===100005)"), 'srv.js 전 다시 걸어도 가족 알림(100005)은 남음')
    ok(not errs, '스크립트 오류 없음 ' + ' | '.join(errs[:2]))
    b.close()
srv.shutdown()
print('가족 프로필:', '흠 ' + str(len(bad)) if bad else '전부 통과')
sys.exit(1 if bad else 0)
