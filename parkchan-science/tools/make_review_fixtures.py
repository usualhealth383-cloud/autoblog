#!/usr/bin/env python3
"""검수용 예시 기록 만들기(2026-10-13) — 외부 검수자(사람·ChatGPT)가 '빈 앱'이 아니라 일주일 넘게 쓴 앱을 보게 한다.

로컬 모드 시연 계정(학생 박○○ DEMO01 · 보호자 · 원장)으로, 고정 시계를 하루씩 넘기며 실제 화면을 눌러 9일을 흘린다.
  1일(월)~4일(목) 공부 · 5일(금) 쉼 · 6~8일 공부 · 9일(화) 저녁 = '오늘'(아직 오늘 공부 전, 복습이 기다림)
  원장: 2일째 공지·과제(OX 5문제) · 7일째 선생님 한 마디 · 학생: 4일째 과제 3/5 · 3일째 시험 일정(범위 통합과학 1, 9일째 기준 D-9)
끝나면 역할마다(학생·보호자·원장) 로그인해 localStorage 의 pcs.* 를 떠서 docs/parkchan/review-fixtures.json 에 쓴다.
review.html 이 이것을 기기에 넣으며 날짜를 '오늘'로 옮긴다(기준일 t0).

사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/make_review_fixtures.py
"""
import asyncio, sys, os, json, datetime as dt, pathlib
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes

APP = 'http://127.0.0.1:8765/index.html?server='
OUT = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'parkchan' / 'review-fixtures.json'
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 5)   # 1일째 = 월요일
T0 = D0 + dt.timedelta(8)   # 9일째(화) = 기록 속 '오늘'
ACC = {'student': ('student@demo.kr', '1234'), 'parent': ('parent@demo.kr', '1234'), 'owner': ('owner@parkchan.kr', '2580')}


def at(n, hh=19, mm=0):
    d = D0 + dt.timedelta(n - 1); return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=KST)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); await ctx.add_init_script(NO_INTRO)
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.clock.set_fixed_time(at(1, 18)); await auto_yes(pg)
        await pg.goto(APP); await pg.wait_for_timeout(900)

        async def login(role):
            if await pg.evaluate('!!ACC'): await logout()
            em, pw = ACC[role]
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)

        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(800)

        async def day(n, hh=19):
            await pg.clock.set_fixed_time(at(n, hh)); await pg.reload(); await pg.wait_for_timeout(1000)
            await pg.evaluate('loadMore()'); await pg.wait_for_function('MORE.ok', timeout=20000)

        async def answer(ok):
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer, n:(q.choices||[]).length }; })()")
            if q['t'] == 'card':
                await pg.click('#csFlip'); await pg.wait_for_timeout(80); await pg.click(f'[data-csr="{"o" if ok else "x"}"]')
            elif q['t'] == 'ox': await pg.click(f'[data-ox="{q["a"] if ok else ("X" if q["a"] == "O" else "O")}"]')
            elif q['t'] == 'blank': await pg.fill('#blankIn', str(q['a']) if ok else '모름'); await pg.click('#blankGo')
            elif q['t'] == 'essay': await pg.click('#essayShow'); await pg.wait_for_timeout(80); await pg.click(f'[data-ess="{"맞음" if ok else "틀림"}"]')
            else: await pg.click(f'[data-bp="{q["a"] if ok else (q["a"] % q["n"]) + 1}"]')
            await pg.wait_for_timeout(120)

        async def run_set(pattern):
            i = 0
            while await pg.evaluate('!!(bs && bs.items[bs.i])'):
                await answer(pattern(i)); await pg.click('#bankNext'); await pg.wait_for_timeout(120); i += 1
            await pg.click('#bankQuit2'); await pg.wait_for_timeout(300)

        async def now():
            return await pg.evaluate("(document.querySelector('#v-today .ps.now')||{}).id || ''")

        async def path(quiz_ok=True, rev=lambda i: i % 4 != 1):
            if await now() == 'ps-read':
                await pg.click('#pRead'); await pg.wait_for_timeout(300); await pg.click('#markDone'); await pg.wait_for_timeout(250)
                await pg.click('#dPathGo'); await pg.wait_for_timeout(300)
            if await now() == 'ps-blank':
                await pg.click('#pBlank'); await pg.wait_for_timeout(200); await pg.click('#bkGo'); await pg.wait_for_timeout(150); await pg.click('#bkDone'); await pg.wait_for_timeout(200)
            if await now() == 'ps-quiz':
                await pg.click('#goQuiz'); await pg.wait_for_timeout(250); a = await pg.evaluate('qState.q.answer')
                await pg.click(f'.opt[data-p="{a if quiz_ok else (1 if a != 1 else 2)}"]'); await pg.wait_for_timeout(250)
                await pg.click('#grade'); await pg.wait_for_timeout(300)
            for _ in range(4):
                if await now() != 'ps-review': break
                await pg.click('#revStart'); await pg.wait_for_timeout(300); await run_set(rev)

        async def practice(n, pattern):
            await pg.evaluate(f"startBank(pickBank({n}), '연습')"); await pg.wait_for_timeout(300); await run_set(pattern)

        async def note(text):
            await pg.evaluate("show('today')"); await pg.wait_for_timeout(200)
            await pg.click('#goNote'); await pg.wait_for_timeout(300); await pg.click('#noteNew'); await pg.wait_for_timeout(300)
            await pg.fill('#nedF0', text); await pg.wait_for_timeout(600); await pg.click('#nedDone'); await pg.wait_for_timeout(400)
            await pg.evaluate("show('today')"); await pg.wait_for_timeout(200)

        # 1일째(월)
        await login('student'); await day(1)
        await path(); await practice(10, lambda i: i % 3 != 2)
        await note('모든 사건은 시간과 공간 좌표로 적는다. 1 m는 빛이 진공에서 1/299,792,458초 동안 가는 거리.')
        # 2일째(화) — 원장: 공지·과제
        await day(2); await path(quiz_ok=False)
        await login('owner'); await day(2, 20)
        await pg.evaluate("(async () => { const st = (await DBX.students()).find(s => s.code === 'DEMO01'); await DBX.sendNotice(st.cls, '토요일 보충 수업 안내', '이번 주 토요일 오후 2시에 I단원 보충 수업이 있어요. 오답 노트를 챙겨 오세요.'); })()")
        await pg.click('[data-adm="asg"]'); await pg.wait_for_selector('#asgForm'); await pg.wait_for_timeout(400)
        await pg.click('#asgForm [data-af="kind"][data-val="bank"]'); await pg.select_option('#afLesson', '1101'); await pg.wait_for_timeout(150)
        await pg.click('#asgForm [data-af="type"][data-val="ox"]'); await pg.click('#asgForm [data-af="n"][data-val="5"]'); await pg.wait_for_timeout(100)
        cls = await pg.evaluate("(async () => (await DBX.students()).find(s => s.code === 'DEMO01').cls)()")
        await pg.select_option('#afCls', cls); await pg.wait_for_timeout(150)
        await pg.fill('#afDue', (D0 + dt.timedelta(9)).isoformat()); await pg.dispatch_event('#afDue', 'change'); await pg.wait_for_timeout(150)
        await pg.click('#afSend'); await pg.wait_for_timeout(1000)
        # 3일째(수) — 학생: 시험 일정
        await login('student'); await day(3); await path(rev=lambda i: i != 0)
        await pg.evaluate(f"S.sched.events.push({{ id:'ev-mid', date:'{(T0 + dt.timedelta(9)).isoformat()}', title:'2학기 중간고사 · 통합과학', kind:'exam', from:'', memo:'I~II단원', scope:{{ book:'1' }} }}); save(S)")
        await note('측정값에는 늘 오차가 있다. 오차 = 측정값 − 참값. 여러 번 재서 평균을 내면 우연 오차가 줄어든다.')
        # 4일째(목) — 과제 3/5 하고 멈춤
        await day(4); await path()
        card = pg.locator('.asgcard').first
        if await card.count():
            await card.click(); await pg.wait_for_timeout(600)
            for k in range(3): await answer(k != 1); await pg.click('#bankNext'); await pg.wait_for_timeout(150)
            await pg.click('#bankQuit'); await pg.wait_for_timeout(800)
        # 5일째(금) 쉼 · 6~7일 공부
        await day(6, 15); await path(); await practice(8, lambda i: i % 4 != 3)
        await day(7, 20); await path(); await note('헷갈림: 기본량 7개 중 광도(cd)와 물질량(mol)의 단위.')
        # 8일째(월) — 원장: 이번 주 선생님 한 마디(그 주 월요일 기준이라 8일째에) · 9일째(화) 저녁 = 오늘(아직 오늘 공부 전)
        await login('student'); await day(8); await path(); await practice(10, lambda i: i % 3 != 0)
        await login('owner'); await day(8, 21)
        await pg.click('[data-adm="students"]'); await pg.wait_for_timeout(500); await pg.click('[data-stu="DEMO01"]'); await pg.wait_for_timeout(700)
        await pg.fill('#noteIn', '지난주 엿새를 꾸준히 했어요. 이번 주엔 틀린 OX 3개만 다시 봐요.'); await pg.click('#noteSave'); await pg.wait_for_timeout(600)
        await pg.evaluate('closeSheet()'); await login('student')
        await day(9, 19)

        dump = "Object.fromEntries(Object.keys(localStorage).filter(k => k.startsWith('pcs.')).map(k => [k, localStorage.getItem(k)]))"
        out = {}
        for role in ('student', 'parent', 'owner'):
            await login(role); await day(9, 19)
            out[role] = await pg.evaluate(dump)
        await logout(); out['guest'] = {}
        info = await pg.evaluate("({ days:S.days, wrong:S.wrong.length })")
        OUT.write_text(json.dumps({'t0': T0.isoformat(), 'made': dt.date.today().isoformat(), 'roles': out}, ensure_ascii=False), encoding='utf-8')
        print('FIXTURES OK', OUT.name, f'{OUT.stat().st_size/1e3:.0f} KB', 'roles', list(out), 'errors', errs[:3])
        await b.close()

asyncio.run(main())
