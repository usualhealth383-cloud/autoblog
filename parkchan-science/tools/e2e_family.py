#!/usr/bin/env python3
"""형제·자매 E2E — 보호자 한 계정에 자녀 둘을 잇고, 이름을 눌러 바꿔 보고, 한 명만 연결 해제한다.
+ 보호자 '이번 주 요약'(벤치마크 ★5) — 공부한 날·개념·문제·정답률 4주·과제·다시 볼 소단원 2 · 확인 전 보호자는 못 봄 · 비교·순위 말 없음

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh 시험대(:8767)에 붙는다.
사용: python3 tools/e2e_family.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes, approve_child, member
SRV = '--server' in sys.argv; GW = 'http://127.0.0.1:8767'
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={json.loads(U.urlopen(GW + '/__anon').read())['anon']}" if SRV else '?server=')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_family'; os.makedirs(SC, exist_ok=True)
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')


async def main():
    if SRV: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        await auto_yes(pg)
        await pg.goto(APP); await pg.wait_for_timeout(700)
        async def login(em, pw):
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1000)
        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(700)
        # 원장: 형제 둘 등록 + 동생만 수동 출석
        await login(*OWNER); codes = []
        for nm, cls in (('형학생', '월목반'), ('동생학생', '화금반')):
            await pg.fill('#stName', nm); await pg.select_option('#stCls', cls); await pg.fill('#stUntil', '2099-12-31'); await pg.click('#stAdd'); await pg.wait_for_timeout(700)
            codes.append(await pg.evaluate('issued.code'))
        await pg.click('[data-adm="attend"]'); await pg.wait_for_timeout(900); await pg.click(f'[data-manual="{codes[1]}"]'); await pg.wait_for_timeout(800)
        await pg.click('[data-adm="sched"]'); await pg.wait_for_timeout(700); await pg.select_option('#scCls', '화금반'); await pg.fill('#scDate', '2099-10-15'); await pg.fill('#scT', '3단원 평가')
        await pg.click('#scSend'); await pg.wait_for_timeout(800)
        await logout()
        # 보호자: 형 코드로 가입 → 동생 추가
        await signup(pg, '형제보호자', 'fam@t.kr', role='parent', child=codes[0])
        assert '원장님 확인을 기다리고' in await pg.locator('#v-parent').inner_text(), '확인 전 안내가 없다'
        await approve_child(pg, codes[0])
        assert await pg.evaluate('view') == 'parent' and '형학생 학생' in await pg.locator('#v-parent').inner_text()
        assert await pg.locator('[data-kid]').count() == 0, '자녀가 하나인데 고르기 칩이 보임'
        await pg.click('#childAdd'); await pg.wait_for_timeout(300)
        await pg.fill('.sheet #childIn', 'ZZZ999'); await pg.click('.sheet #childGo'); await pg.wait_for_timeout(600)
        assert '등록되지 않은' in await pg.locator('#childAddErr').inner_text(), '시트 안에 오류가 안 뜸'
        await pg.fill('.sheet #childIn', codes[1]); await pg.click('.sheet #childGo'); await pg.wait_for_timeout(1400)
        await approve_child(pg, codes[1])
        assert await pg.locator('#sheetBg').count() == 0 and await pg.locator('[data-kid]').count() == 2, '자녀 고르기 칩이 두 개가 아님'
        await pg.click(f'[data-kid="{codes[1]}"]'); await pg.wait_for_timeout(900)
        body = await pg.locator('#v-parent').inner_text(); assert '동생학생 학생' in body and '출석' in body, body[:200]
        await pg.screenshot(path=f'{SC}/f01_two_kids.png', full_page=True)
        await pg.click(f'[data-kid="{codes[0]}"]'); await pg.wait_for_timeout(900)
        body = await pg.locator('#v-parent').inner_text(); assert '형학생 학생' in body and '아직 출석 전' in body, body[:200]
        # 이번 주 요약: 최근 7일 띠 · 세 가지 수 · 노트는 보이지 않음
        assert await pg.locator('.pweek .week .d').count() == 7 and await pg.locator('.pweek .pstat > div').count() == 3, '이번 주 요약이 없음'
        assert '공부한 날' in await pg.locator('.pweek').inner_text() and '연속' not in await pg.locator('.pweek').inner_text() and '공부 노트' not in (t := await pg.locator('.pweek').inner_text()) and '메모' not in t
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); assert '2명' in await pg.locator('#v-me').inner_text()
        # 보호자 일정 화면에 동생 반 일정이 이름과 함께
        await pg.evaluate("planDay = '2099-10-15'"); await pg.click('.tab[data-v="plan"]'); await pg.wait_for_timeout(900)
        assert await pg.evaluate("acadEvents.some(e => e.title === '동생학생 · 3단원 평가')"), await pg.evaluate('acadEvents')
        # 비밀번호 바꾸기 → 새 비밀번호로만 로그인
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#pwOpen')
        await pg.fill('#pwNew', 'newpass77'); await pg.fill('#pwNew2', 'newpass78'); await pg.click('#pwSave'); assert '다릅니다' in await pg.locator('#pwErr').inner_text()
        await pg.fill('#pwNew2', 'newpass77'); await pg.click('#pwSave'); await pg.wait_for_timeout(800); assert await pg.locator('#sheetBg').count() == 0
        await logout(); await login('fam@t.kr', 'pass1234'); assert '다릅니다' in await pg.locator('.auth .err').inner_text(), '옛 비밀번호로 로그인됨'
        await pg.fill('#lgPw', 'newpass77'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200); assert await pg.evaluate('view') == 'parent'
        # 동생만 연결 해제 → 형만 남음
        await pg.click('.tab[data-v="parent"]'); await pg.wait_for_timeout(600); await pg.click(f'[data-kid="{codes[1]}"]'); await pg.wait_for_timeout(800)
        await pg.click('#unlinkChild'); await pg.wait_for_timeout(1000)
        assert await pg.locator('[data-kid]').count() == 0 and '형학생 학생' in await pg.locator('#v-parent').inner_text(), '한 명만 해제가 안 됨'
        assert await pg.evaluate('ACC.childCodes.length') == 1
        # 원장 학생 상세: 형에게 보호자 1명, 동생 0명
        await logout(); await login(*OWNER); await pg.click('[data-adm="students"]'); await pg.wait_for_timeout(700)
        await pg.click(f'[data-stu="{codes[0]}"]'); await pg.wait_for_timeout(800); assert '보호자 1명' in await pg.locator('.sheet').inner_text(); await pg.click('#sheetClose')
        await pg.click(f'[data-stu="{codes[1]}"]'); await pg.wait_for_timeout(800); assert '보호자 0명' in await pg.locator('.sheet').inner_text()
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'FAMILY E2E OK · 콘솔 오류', errs); await b.close()

async def guardian_talk():
    """보호자가 직접 '이야기 끄기'(docs/11 §12-15) — 쓰기만 끄기 → 자녀는 읽기만(서버도 막음) → 읽기까지 끄기 → 자녀 화면은 차분한 안내 한 장 → 다시 켜기"""
    if SRV: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700)
        async def login(em, pw):
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1000)
        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(700)
        async def as_student():
            await logout(); await login('gt-kid@t.kr', 'pass1234'); await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(900)
        async def as_parent(mode):
            await logout(); await login('gt-mom@t.kr', 'pass1234'); await pg.click('.tab[data-v="parent"]'); await pg.wait_for_timeout(900)
            await pg.click('#ptTalk'); await pg.wait_for_timeout(300); await pg.click(f'[data-ptm="{mode}"]')
            if mode == 'write': await pg.screenshot(path=f'{SC}/g02_talk_sheet.png')
            await pg.click('#ptGo'); await pg.wait_for_timeout(900)
        await login(*OWNER); await pg.fill('#stName', '이야기학생'); await pg.select_option('#stCls', '월목반'); await pg.fill('#stUntil', '2099-12-31'); await pg.click('#stAdd'); await pg.wait_for_timeout(700)
        code = await pg.evaluate('issued.code')
        await logout(); await signup(pg, '이야기학생', 'gt-kid@t.kr', code=code); await member(pg)
        await pg.evaluate("DBX.setNick('이야기꾼').then(a => ACC = a)"); await pg.wait_for_timeout(300)
        await pg.evaluate("DBX.addPost({ board:'talk', title:'보이는 글', body:'보호자 설정 전에 쓴 글' })"); await pg.wait_for_timeout(300)
        await logout(); await signup(pg, '이야기보호자', 'gt-mom@t.kr', role='parent', child=code); await approve_child(pg, code)
        t = await pg.inner_text('#ptTalkSec'); assert '켜 둠' in t and await pg.locator('#ptTalk').count() == 1, t
        await pg.screenshot(path=f'{SC}/g01_parent_talk.png', full_page=True)
        await as_parent('write'); t = await pg.inner_text('#ptTalkSec'); assert '쓰기 꺼 둠' in t, t
        await as_student()
        g = await pg.inner_text('#talkGate'); assert '보호자와 정한' in g and await pg.locator('#postNew').count() == 0 and await pg.locator('.pcard').count() >= 1, g
        await pg.screenshot(path=f'{SC}/g03_kid_write_off.png')
        r = await pg.evaluate("DBX.addPost({ board:'talk', title:'우회', body:'써지면 안 됩니다' }).then(() => 'ok', e => e.message)"); assert '보호자와 정한' in r, ('쓰기를 서버·기기가 막아야 함', r)
        await as_parent('all'); assert '쓰기·읽기 꺼 둠' in await pg.inner_text('#ptTalkSec')
        await as_student()
        assert await pg.locator('#talkRest').count() == 1 and await pg.locator('.pcard').count() == 0, '읽기까지 껐는데 글이 보임'
        assert '보호자와 정한' in await pg.inner_text('#talkRest')
        n = await pg.evaluate("DBX.posts('전체','').then(l => l.length)"); assert n == 0, ('서버도 글을 주지 않아야 함', n)
        await pg.screenshot(path=f'{SC}/g04_kid_read_off.png')
        await as_parent('on'); assert '켜 둠' in await pg.inner_text('#ptTalkSec')
        await as_student(); assert await pg.locator('#postNew').count() == 1 and await pg.locator('.pcard').count() >= 1, '다시 켰는데 글쓰기가 안 열림'
        # 원장 화면: 보호자가 끈 학생 · 처리 기록(보호자)
        await as_parent('write'); await logout(); await login(*OWNER); await pg.click('[data-adm="talk"]'); await pg.wait_for_timeout(900)
        t = await pg.inner_text('#guardList'); assert '이야기학생' in t and '쓰기만 끔' in t and '이야기보호자' in t, t
        await pg.click('#logBox summary'); await pg.wait_for_timeout(200); t = await pg.inner_text('#logBox'); assert '보호자가 쓰기 끔' in t and '보호자 이야기보호자' in t, t
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'GUARDIAN TALK E2E OK'); await b.close()

async def weekly():
    """보호자 '이번 주 요약'(★5) — 자녀 진도(dq·dc·wrong)와 과제 제출로 계산. 확인 전 보호자에게는 열리지 않는다."""
    import datetime as dt
    from zoneinfo import ZoneInfo
    T = dt.datetime.now(ZoneInfo('Asia/Seoul')).date(); mon = T - dt.timedelta(days=T.isoweekday() - 1); D = lambda n: (mon + dt.timedelta(days=n)).isoformat()
    days = sorted({mon.isoformat(), T.isoformat()})
    prog = {'days': [D(-9)] + days, 'done': ['x'], 'dq': {D(0): [10, 7], D(-7): [10, 6], D(-14): [5, 4]}, 'dc': {D(0): 3, D(-7): 5},
            'wrong': [{'l': '1102', 'n': i, 'iso': D(-3), 'a': D(-3), 'd': D(1), 'x': 1, 'k': 1} for i in (1, 2, 3)] + [{'l': '1101', 'n': 1, 'iso': D(-3), 'a': D(-3), 'd': D(2), 'x': 1, 'k': 1},
                      {'l': '1103', 'n': 1, 'iso': D(-3), 'a': D(-3), 'd': D(2), 'x': 1, 'k': 1, 'cleared': True}], 'stats': {'a': 25, 'c': 17}}
    if SRV:
        U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
        keys = json.loads(U.urlopen(GW + '/__anon').read())
        def rest(path, body, method='POST', tok=None, prefer='return=minimal'):
            h = {'Content-Type': 'application/json', 'apikey': keys['anon'], 'Authorization': 'Bearer ' + (tok or keys['service']), 'Prefer': prefer}
            r = U.urlopen(U.Request(GW + path, data=json.dumps(body).encode(), headers=h, method=method)).read(); return json.loads(r) if r else None
        rest('/rest/v1/students', [{'code': 'WEEK01', 'name': '요약학생', 'cls': '월목반', 'until': '2099-02-28'}])
        rest('/rest/v1/progress', {'code': 'WEEK01', 'state': prog})
        own = json.loads(U.urlopen(U.Request(GW + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json', 'apikey': keys['anon']}, method='POST')).read())['access_token']
        aid = rest('/rest/v1/rpc/assign_create', {'p_kind': 'bank', 'p_title': '이번 주 과제', 'p_ref': '1101', 'p_items': ['1101-q1', '1101-q2'], 'p_cls': '월목반', 'p_codes': None, 'p_due': D(6)}, tok=own)['id']
        import psycopg2; c = psycopg2.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs'); c.autocommit = True
        c.cursor().execute("insert into submissions(aid, code, done, right_n, secs, submitted_at) values (%s, 'WEEK01', 2, 2, 40, now())", (aid,)); c.close()
        code = 'WEEK01'
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        shots = []
        for color in ('light', 'dark'):
            ctx = await b.new_context(viewport={'width': 400, 'height': 1600}, color_scheme=color); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700)
            if not SRV:
                code = 'DEMO01'
                await pg.evaluate("""([prog, due]) => { if (!localStorage.getItem('pcs.db.v2')) DBX.removeClass('__없음__'); const d = JSON.parse(localStorage.getItem('pcs.db.v2'));
                  d.progress.DEMO01 = { ...prog, at:new Date().toISOString() };
                  d.asg = [{ id:'a-week', kind:'bank', title:'이번 주 과제', ref:'1101', items:['1101-q1','1101-q2'], cls:'월목반', codes:['DEMO01','MON123'], due, at:new Date().toISOString() }];
                  d.subs = [{ aid:'a-week', code:'DEMO01', done:2, right:2, secs:40, wrong:[], submitted_at:new Date().toISOString(), late:false }];
                  localStorage.setItem('pcs.db.v2', JSON.stringify(d)); }""", [prog, D(6)])
                await pg.reload(); await pg.wait_for_timeout(700)
                await pg.click('#goLogin'); await pg.fill('#lgEmail', 'parent@demo.kr'); await pg.fill('#lgPw', '1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(1300)
            elif color == 'light':
                # 확인 전 보호자: 요약이 열리지 않는다
                await signup(pg, '요약보호자', 'wk-mom@t.kr', role='parent', child=code)
                assert '원장님 확인을 기다리고' in await pg.inner_text('#v-parent') and await pg.locator('#weekSum').count() == 0, '확인 전인데 요약이 보임'
                n = await pg.evaluate("DBX.childAssignments('WEEK01').then(r => r.ok)"); assert n is False, '확인 전 보호자가 과제를 받음'
                await approve_child(pg, code)
            else:
                await pg.click('#goLogin'); await pg.fill('#lgEmail', 'wk-mom@t.kr'); await pg.fill('#lgPw', 'pass1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(1300)
            assert await pg.evaluate('view') == 'parent', await pg.evaluate('view')
            await pg.wait_for_selector('#weekSum')
            w = await pg.inner_text('#weekSum')
            assert '이번 주 요약' in w and f'{len(days)}/7일' in w.replace('\n', '') and '3개' in w and '10문제' in w.replace('\n', ''), w
            lab = await pg.get_attribute('#weekSum .tbars', 'aria-label')
            assert '이번 주 70%' in lab and '60%' in lab and '80%' in lab and '푼 문제 없음' in lab and await pg.locator('#weekSum .tb').count() == 4, lab
            assert '1개 중 1개 냈어요' in w and '이번 주 과제' in w, w
            ag = await pg.locator('#weekSum .wl').all_inner_texts()
            assert len(ag) == 2 and 'I-02' in ag[0] and '다시 볼 문제 3' in ag[0] and 'I-01' in ag[1], ag
            assert all(x not in w for x in ('연속', '순위', '평균', '등수', '반에서')) and '견주지 않고' in w, w
            await pg.wait_for_timeout(2500); await pg.locator('#weekSum').screenshot(path=f'{SC}/w01_week_{color}.png'); shots.append(color)
            await ctx.close()
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'WEEKLY SUMMARY E2E OK', shots); await b.close()

asyncio.run(main()); asyncio.run(guardian_talk()); asyncio.run(weekly())
