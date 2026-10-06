#!/usr/bin/env python3
"""학원 과제 E2E(벤치마크 ★4) — 원장이 내고 → 학생 오늘 화면 카드(마감 D-n · 진행 n/N) → 풀면 학원으로 → 원장 제출 현황 · '처리할 것'.

· 원장 › 과제: 소단원 문제 N개(유형·난이도) · 개념 읽기 · 모의고사 회차 · 마감일 → 반(또는 학생 고르기)에 내기
· 학생: 오늘 화면 맨 위 카드(2개까지 + '더 있습니다') · 중간에 그만두면 이어서 · 끝까지 풀면 맞힌 수·걸린 시간·제출 시각이 서버로
· 개념 읽기: 개념 화면 위에 '학원 과제 · 개념 읽기 n/N' · '읽었어요 · 다음 개념' → 마지막은 '과제 내기'
· 모의고사: 제출하면 학원 과제로도 냄 · 마감 지난 과제는 '늦게 냄' · 망이 끊기면 기기에 두었다가 다시 보냄
· 원장: 목록(제출 n/N · 정답률 · 아직 안 낸 수) · 제출 현황(학생별 · 많이 틀린 문항 3) · '처리할 것'에 '마감 지남 · 아직 안 냄'(과제 보기)
· 로컬: 같은 기기 시연 계정(원장·학생) · --server: 시험대(:8767), 학생은 학원 코드로 가입

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh.   사용: python3 tools/e2e_assign.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt, urllib.request as U
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes, signup
SRV = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
KEYS = json.loads(U.urlopen(GW + '/__anon').read()) if SRV else {}
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={KEYS['anon']}" if SRV else '?server=')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_assign'; os.makedirs(SC, exist_ok=True)
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')
STUDENT = ('asg-stu@t.kr', 'pass1234') if SRV else ('student@demo.kr', '1234')
T = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()
D = lambda n: (T + dt.timedelta(days=n)).isoformat()
WD = '월화수목금토일'


def rest(path, body=None, method='GET', prefer='return=minimal'):
    h = {'Content-Type': 'application/json', 'apikey': KEYS['anon'], 'Authorization': 'Bearer ' + KEYS['service'], 'Prefer': prefer}
    r = U.urlopen(U.Request(GW + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)).read()
    return json.loads(r) if r else None


def sql(q, *a):
    import psycopg2
    c = psycopg2.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs'); c.autocommit = True
    cur = c.cursor(); cur.execute(q, a)
    try: return cur.fetchall()
    except Exception: return None
    finally: c.close()


async def main():
    if SRV:
        U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
        rest('/rest/v1/students', [{'code': 'E2EA01', 'name': '과제학생', 'cls': '월목반', 'phone': '01011112222', 'until': '2099-02-28'},
                                   {'code': 'E2EA02', 'name': '안낸학생', 'cls': '월목반', 'phone': '01033334444', 'until': '2099-02-28'},
                                   {'code': 'E2EA03', 'name': '다른반학생', 'cls': '화금반', 'phone': '', 'until': '2099-02-28'}], 'POST')
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text and 'Failed to fetch' not in m.text else None)
        await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700)

        async def login(em, pw):
            if await pg.locator('#goLogin').count() == 0 and await pg.evaluate('!!ACC'): await logout()
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1300)

        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(800)

        async def asg_tab():
            await pg.click('[data-adm="asg"]'); await pg.wait_for_selector('#asgForm'); await pg.wait_for_function('MORE.ok', timeout=20000); await pg.wait_for_timeout(500)

        async def give(kind, due, lesson=None, n=None, cls='월목반', mock=None, typ=None):
            await pg.click(f'#asgForm [data-af="kind"][data-val="{kind}"]'); await pg.wait_for_timeout(150)
            if lesson: await pg.select_option('#afLesson', lesson); await pg.wait_for_timeout(150)
            if typ: await pg.click(f'#asgForm [data-af="type"][data-val="{typ}"]'); await pg.wait_for_timeout(100)
            if n: await pg.click(f'#asgForm [data-af="n"][data-val="{n}"]'); await pg.wait_for_timeout(100)
            if mock: await pg.select_option('#afMock', mock); await pg.wait_for_timeout(150)
            await pg.select_option('#afCls', cls); await pg.wait_for_timeout(150)
            await pg.fill('#afDue', due); await pg.dispatch_event('#afDue', 'change'); await pg.wait_for_timeout(150)
            summ = await pg.inner_text('#afSum')
            await pg.click('#afSend'); await pg.wait_for_timeout(1100)
            return summ

        # ── 1. 원장: 과제 네 개 내기 ──
        await login(*OWNER); assert await pg.evaluate('view') == 'admin', await pg.evaluate('view')
        segs = await pg.evaluate("[...document.querySelectorAll('.seg.adm button')].map(b => [b.textContent, b.getBoundingClientRect().width, b.scrollWidth <= b.clientWidth + 1])")
        assert any(t == '과제' for t, *_ in segs) and all(fit for *_, fit in segs), ('원장 탭에 과제 · 글자가 넘치지 않음', segs)
        await asg_tab()
        L1, L2 = await pg.evaluate("[lessonName('1101'), lessonName('1102')]")
        assert '과제 내기' in await pg.inner_text('#asgForm') and '아직 낸 과제가 없습니다' in await pg.inner_text('#v-admin')
        s1 = await give('bank', D(2), lesson='1101', n='5', typ='ox')
        assert '문제 5개 (OX)' in s1 and '월목반 2명' in s1 and '23:59까지' in s1, s1
        await pg.screenshot(path=f'{SC}/a01_owner_form.png', full_page=True)
        s2 = await give('read', D(3), lesson='1101'); assert '개념' in s2 and '읽기' in s2, s2
        s3 = await give('mock', D(5), mock='1'); assert '모의고사 · 통합과학 1' in s3, s3
        s4 = await give('bank', D(0), lesson='1102', n='5')          # 마감 지남으로 만들 과제
        lst = await pg.inner_text('#v-admin'); assert '낸 과제 4개' in lst and lst.count('제출 0 / 2명') == 4, lst
        # 학생 고르기 — 다른 반 학생 한 명에게만
        await pg.click('#asgForm [data-af="kind"][data-val="bank"]'); await pg.select_option('#afLesson', '1103'); await pg.wait_for_timeout(150)
        await pg.select_option('#afCls', '학생 고르기'); await pg.wait_for_timeout(250)
        assert await pg.locator('#asgForm [data-apick]').count() >= 3, '학생 고르기 목록이 없음'
        other = 'E2EA03' if SRV else 'TUE456'
        await pg.check(f'#asgForm [data-apick][value="{other}"]'); await pg.wait_for_timeout(200)
        assert '학생 1명' in await pg.inner_text('#afSum'), await pg.inner_text('#afSum')
        await pg.click('#afSend'); await pg.wait_for_timeout(1000)
        assert '낸 과제 5개' in await pg.inner_text('#v-admin') and '학생 1명' in await pg.inner_text('#v-admin')
        await pg.screenshot(path=f'{SC}/a02_owner_list_light.png', full_page=True)
        # 마감 지난 과제(오늘 마감으로 낸 것을 어제로)
        if SRV: sql("update assignments set due = current_date - 1 where title like %s", L2 + '%')
        else:
            await pg.evaluate("t => { const d = JSON.parse(localStorage.getItem('pcs.db.v2')); d.asg.forEach(a => { if (a.title.startsWith(t)) a.due = addDays(todayISO(), -1); }); localStorage.setItem('pcs.db.v2', JSON.stringify(d)); }", L2)
            await pg.reload(); await pg.wait_for_timeout(1000)
        # ── 2. 학생: 오늘 화면 카드 ──
        if SRV:
            await logout(); await signup(pg, '과제학생', STUDENT[0], code='E2EA01')
        else:
            await login(*STUDENT)
        if await pg.evaluate('view') != 'today': await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(900)
        await pg.wait_for_selector('.asgcard')
        cards = await pg.locator('.asgcard').all_inner_texts()
        assert len(cards) == 2 and '마감 지남' in cards[0] and '늦게 내도 받아요' in cards[0] and '0/5' in cards[0], cards
        assert '오늘 마감' in cards[1] or 'D-2' in cards[1], cards
        assert '학원 과제가 2개 더 있어요' in await pg.inner_text('#v-today'), '두 개 넘으면 한 줄로 알림'
        assert '다른 반' not in ''.join(cards) and await pg.evaluate("ASG.length") == 4, ('골라 낸 다른 반 과제는 안 보임', await pg.evaluate('ASG.map(a=>a.title)'))
        order = await pg.evaluate("(() => { const a = document.querySelector('.asgcard'), r = document.querySelector('#v-today .rhythm'), c = document.querySelector('#v-today .path'); return !!(a && r && c && (a.compareDocumentPosition(r) & 4) && (a.compareDocumentPosition(c) & 4)); })()")
        assert order, '과제 카드는 리듬·오늘 개념보다 위'
        hs = await pg.evaluate("[...document.querySelectorAll('.asgcard')].map(e => e.getBoundingClientRect().height)"); assert min(hs) >= 44, hs
        await pg.screenshot(path=f'{SC}/a03_student_today_light.png')

        async def answer(correct=True):
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer, n:(q.choices||[]).length }; })()")
            if q['t'] == 'ox':
                v = q['a'] if correct else ('X' if q['a'] == 'O' else 'O'); await pg.click(f'[data-ox="{v}"]')
            elif q['t'] in ('mc', 'multi'):
                v = q['a'] if correct else (q['a'] % q['n']) + 1; await pg.click(f'[data-bp="{v}"]')
            elif q['t'] == 'blank':
                await pg.fill('#blankIn', str(q['a']) if correct else '모름'); await pg.click('#blankGo')
            else:
                await pg.click('#essayShow'); await pg.wait_for_timeout(100); await pg.click(f'[data-ess="{"맞음" if correct else "틀림"}"]')
            await pg.wait_for_timeout(250)

        # ── 3. 소단원 문제 5개: 2개 풀고 그만두기 → 이어서 → 끝 ──
        await pg.locator('.asgcard', has_text=L1 + ' · 문제').click(); await pg.wait_for_timeout(700)
        assert await pg.evaluate("bs && bs.kind") == 'asg' and await pg.evaluate('bs.items.length') == 5
        await answer(True); await pg.click('#bankNext'); await answer(False); await pg.click('#bankNext'); await pg.wait_for_timeout(300)
        await pg.click('#bankQuit'); await pg.wait_for_timeout(1000)
        assert await pg.evaluate('view') == 'today'
        c = await pg.locator('.asgcard', has_text=L1 + ' · 문제').inner_text(); assert '2/5' in c, c
        if SRV:
            r = sql("select done, right_n, submitted_at from submissions s join assignments a on a.id = s.aid where a.title like %s", L1 + '%문제%')
            assert r and r[0][0] == 2 and r[0][1] == 1 and r[0][2] is None, ('진행이 서버에 남음', r)
        await pg.locator('.asgcard', has_text=L1 + ' · 문제').click(); await pg.wait_for_timeout(600)
        assert await pg.evaluate('bs.i') == 2, '이어서 풀기가 아님'
        for k in range(3):
            await answer(k != 1)
            await pg.click('#bankNext'); await pg.wait_for_timeout(250)
        await pg.wait_for_timeout(900)
        res = await pg.inner_text('#v-bank'); assert '3 / 5' in res and '학원에 냈습니다' in res and '틀린 문제 2' in res, res
        await pg.screenshot(path=f'{SC}/a04_bank_result.png', full_page=True)
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(900)
        assert await pg.locator('.asgcard', has_text=L1 + ' · 문제').count() == 0, '낸 과제가 카드에 남음'
        # ── 4. 개념 읽기 ──
        await pg.locator('.asgcard', has_text='읽기').click(); await pg.wait_for_timeout(800)
        assert await pg.evaluate('view') == 'detail' and await pg.locator('.asgbar').count() == 1 and await pg.locator('#markDone').count() == 0
        n = await pg.evaluate("ASG.find(a => a.kind === 'read').n"); assert '1 / ' + str(n) in (await pg.inner_text('.asgbar')).replace('\n', ' '), await pg.inner_text('.asgbar')
        await pg.screenshot(path=f'{SC}/a05_read_bar.png')
        for i in range(n):
            btn = await pg.inner_text('#asgReadNext'); assert ('과제 내기' in btn) == (i == n - 1), btn
            await pg.click('#asgReadNext'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('view') == 'today'; await pg.wait_for_timeout(800)
        assert await pg.locator('.asgcard', has_text='읽기').count() == 0, '읽기 과제가 남음'
        # ── 5. 마감 지난 과제: 망이 끊긴 채 끝냄 → 기기에 두었다가 → 다시 보냄(늦게 냄) ──
        await pg.evaluate("(() => { window.__realSave = DBX.assignSave; DBX.assignSave = async () => { throw Object.assign(new Error('net'), { net:true }); }; })()")
        await pg.locator('.asgcard', has_text=L2).click(); await pg.wait_for_timeout(600)
        for k in range(await pg.evaluate('bs.items.length')):
            await answer(True); await pg.click('#bankNext'); await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(600)
        assert '인터넷이 연결되면' in await pg.inner_text('#asgSent'), await pg.inner_text('#asgSent')
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(900)
        c = await pg.locator('.asgcard', has_text=L2).inner_text(); assert '인터넷이 연결되면' in c, c
        await pg.evaluate("(() => { DBX.assignSave = window.__realSave; })()"); await pg.evaluate('renderToday()'); await pg.wait_for_timeout(1200)
        assert await pg.locator('.asgcard', has_text=L2).count() == 0, '다시 연결됐는데 안 보냄'
        assert await pg.evaluate("Object.values(S.aq).some(q => q.ok && q.late)"), '늦은 제출 표시가 없음'
        # ── 6. 모의고사 ──
        await pg.locator('.asgcard', has_text='모의고사').click(); await pg.wait_for_timeout(900)
        assert await pg.evaluate('mx && mx.asg') and await pg.evaluate('mx.items.length') == 25
        await pg.evaluate("mx.items.forEach((q, i) => { mx.picks[i] = i < 20 ? q.answer : (q.answer % 5) + 1; }); renderMock()")
        await pg.click('#mxSubmit'); await pg.wait_for_timeout(1500)
        t = await pg.inner_text('#v-bank'); assert '학원 과제 · 학원에 냈습니다' in t, t[:300]
        await pg.click('#mockClose'); await pg.wait_for_timeout(900); assert await pg.evaluate('view') == 'today'
        assert await pg.locator('.asgcard').count() == 0, '모든 과제를 냈는데 카드가 남음'
        dark = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme='dark')
        # ── 7. 원장: 제출 현황 · 처리할 것 ──
        await logout(); await login(*OWNER); await asg_tab()
        lst = await pg.inner_text('#v-admin')
        assert '제출 1 / 2명 · 정답률 60%' in lst and '제출 1 / 2명 · 정답률 100% · 늦은 제출 1 · 아직 1명' in lst and '제출 1 / 2명 · 정답률 80%' in lst, lst
        await pg.locator('.asgsentrow', has_text=L1 + ' · 문제').locator('[data-asgrep]').click(); await pg.wait_for_timeout(800)
        sh = await pg.inner_text('.sheet')
        assert '많이 틀린 문항' in sh and '1명 틀림' in sh and '3/5' in sh and '아직' in sh and '냄' in sh, sh
        assert await pg.locator('.sheet .asgtop .kv').count() == 2, '틀린 문항 2개(학생 1명이 2문항 틀림)'
        nophone = await pg.locator('.sheet a[href^="sms:"]').count(); assert nophone == (1 if SRV else 0), '아직 안 낸 학생에게 문자(연락처 있을 때만)'
        await pg.screenshot(path=f'{SC}/a06_report_light.png', full_page=True)
        await pg.click('#sheetClose'); await pg.wait_for_timeout(300)
        await pg.locator('.asgsentrow', has_text=L2).locator('[data-asgrep]').click(); await pg.wait_for_timeout(700)
        assert '늦게 냄' in await pg.inner_text('.sheet'); await pg.click('#sheetClose')
        await pg.click('[data-adm="students"]'); await pg.wait_for_selector('#todoBox')
        rows = await pg.locator('#todoBox .todo-row', has_text='마감 지남').all()
        assert len(rows) >= 1, await pg.inner_text('#todoBox')
        tr = rows[0]; assert '아직 안 냄' in await tr.inner_text() and (await tr.locator('.todo-act').inner_text()).strip() == '과제 보기', await tr.inner_text()
        assert len(rows) == 1, ('마감 지난 미제출은 안 낸 학생 한 명뿐', [await r.inner_text() for r in rows])
        if SRV: assert '안낸학생' in await tr.inner_text()
        await pg.locator('#todoBox').screenshot(path=f'{SC}/a07_todo.png')
        await tr.locator('.todo-act').click(); await pg.wait_for_timeout(800); assert L2 in await pg.inner_text('.sheet'), '과제 보기 → 제출 현황'
        await pg.click('#sheetClose')
        # 어두운 화면 — 원장 과제 탭 · 학생 카드
        dpg = await dark.new_page(); await dark.add_init_script(NO_INTRO); await auto_yes(dpg)
        await dpg.goto(APP); await dpg.wait_for_timeout(700)
        if not SRV:   # 로컬 저장소는 컨텍스트마다 따로 — 같은 기록을 옮긴다
            db = await pg.evaluate("localStorage.getItem('pcs.db.v2')"); await dpg.evaluate("v => localStorage.setItem('pcs.db.v2', v)", db); await dpg.reload(); await dpg.wait_for_timeout(700)
        await dpg.click('#goLogin'); await dpg.fill('#lgEmail', OWNER[0]); await dpg.fill('#lgPw', OWNER[1]); await dpg.click('#lgGo'); await dpg.wait_for_timeout(1300)
        await dpg.click('[data-adm="asg"]'); await dpg.wait_for_selector('#asgForm'); await dpg.wait_for_function('MORE.ok', timeout=20000); await dpg.wait_for_timeout(400)
        await dpg.screenshot(path=f'{SC}/a08_owner_dark.png', full_page=True)
        await dpg.locator('.asgsentrow').first.locator('[data-asgrep]').click(); await dpg.wait_for_timeout(700); await dpg.screenshot(path=f'{SC}/a09_report_dark.png')
        await dpg.click('#sheetClose')
        # 새 과제 하나 → 학생 카드(어두운 화면)
        await dpg.click('#asgForm [data-af="kind"][data-val="read"]'); await dpg.select_option('#afCls', '월목반'); await dpg.wait_for_timeout(150); await dpg.click('#afSend'); await dpg.wait_for_timeout(1000)
        await dpg.click('.tab[data-v="me"]'); await dpg.wait_for_timeout(300); await dpg.click('#logout'); await dpg.wait_for_timeout(800)
        await dpg.click('#goLogin'); await dpg.fill('#lgEmail', STUDENT[0]); await dpg.fill('#lgPw', STUDENT[1]); await dpg.click('#lgGo'); await dpg.wait_for_timeout(1500)
        await dpg.wait_for_selector('.asgcard'); await dpg.screenshot(path=f'{SC}/a10_student_today_dark.png')
        await dark.close()
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'ASSIGN E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
