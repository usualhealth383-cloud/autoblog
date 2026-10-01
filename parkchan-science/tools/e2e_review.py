#!/usr/bin/env python3
"""복습 E2E — 간격을 넓혀 가는 복습(상자 1·3·7·14·30일) · 오늘의 복습(섞어 풀기) · 이번 주 리듬 · 차분한 알림.

날짜는 Playwright 의 고정 시계(clock.set_fixed_time)로 옮긴다 — 앱의 todayISO()·addDays() 가 그대로 따라온다.
· 문제 은행 오답 → 다음 날 기한 · 맞히면 다음 상자 · 틀리면 상자 1 · 7일 넘는 간격에서 두 번 잇달아 맞혀야 정리됨
· 범위에 든 시험이 있으면 간격을 남은 날의 20 %(최소 1일)로 · 하루 복습 10개(밀린 것부터) · 6번 넘게 틀린 문제는 개념 카드로
· 옛 오답 기록(3일 뒤 한 번) → 상자 1(날짜 보존) · 오늘의 복습: 기한 3 + 다른 소단원 2, 같은 소단원이 잇달아 나오지 않음
· 이번 주 리듬(점 7개, 연속 일수 없음) · 알림 3일 무반응이면 멈추고 내 정보에 한 번만 알림(가짜 LocalNotifications)

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_review.py [--shots 폴더]
"""
import asyncio, sys, os, re, json, datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_review'; os.makedirs(SC, exist_ok=True)
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 5)            # 월요일
STREAK = re.compile(r'연속\s?학습|연속\s?일수|\d+\s?일째')


def at(day, hh=12):
    return dt.datetime(day.year, day.month, day.day, hh, 0, tzinfo=KST)


def iso(day):
    return day.isoformat()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []

        async def page(color='light', init=None, stub=None, when=D0):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color)
            await ctx.add_init_script(NO_INTRO)
            if init: await ctx.add_init_script(init)
            if stub: await ctx.add_init_script(stub)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await pg.clock.set_fixed_time(at(when))
            await auto_yes(pg)
            await pg.goto(APP); await pg.wait_for_timeout(600)
            return pg

        async def goto_day(pg, day):
            await pg.clock.set_fixed_time(at(day))
            assert await pg.evaluate('todayISO()') == iso(day)
            await pg.evaluate("dayRoll(); qState = null; if (bs && bs.kind === 'review') bs = null; revHold = null; show('today')"); await pg.wait_for_timeout(250)

        async def answer(pg, ok):
            """문제 은행 화면의 지금 문제를 맞게/틀리게 푼다(유형 무관)"""
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { type:q.type, answer:q.answer, n:(q.choices||[]).length }; })()")
            if q['type'] == 'ox':
                await pg.click(f'[data-ox="{q["answer"] if ok else ("X" if q["answer"] == "O" else "O")}"]')
            elif q['type'] in ('mc', 'multi'):
                a = int(q['answer']); await pg.click(f'[data-bp="{a if ok else (1 if a != 1 else 2)}"]')
            elif q['type'] == 'blank':
                await pg.fill('#blankIn', str(q['answer']) if ok else '모르겠음'); await pg.click('#blankGo')
            else:
                await pg.click('#essayShow'); await pg.wait_for_timeout(100); await pg.click(f'[data-ess="{"맞음" if ok else "틀림"}"]')
            await pg.wait_for_timeout(150)

        async def visible_text(pg):
            return await pg.evaluate("document.querySelector('main').innerText")

        # ───────── 1) 학생(시연 계정) — 문제 은행 오답이 다음 날 돌아온다 ─────────
        s = await page()
        await s.click('#goLogin'); await s.fill('#lgEmail', 'student@demo.kr'); await s.fill('#lgPw', '1234'); await s.click('#lgGo'); await s.wait_for_timeout(900)
        assert await s.evaluate('view') == 'today'
        await s.evaluate('loadMore()'); await s.wait_for_function('MORE.ok', timeout=15000)
        assert await s.locator('#revStart').count() == 0 and await s.locator('.revcard').count() == 0, '아무것도 안 배웠는데 오늘의 복습이 보임'
        L1 = await s.evaluate('todayConcept().lessonId')
        qid = await s.evaluate(f"BANK.find(q => q.lessonId === '{L1}' && q.type === 'ox').id")
        await s.evaluate(f"startBank([BANK.find(q => q.id === '{qid}')], '')"); await s.wait_for_timeout(200)
        await answer(s, False)
        assert '내일' in await s.locator('#v-bank .again').inner_text(), '틀린 뒤 "내일 다시" 안내가 없음'
        w = await s.evaluate(f"findW({{ b:'{qid}' }})")
        assert w['x'] == 1 and w['d'] == iso(D0 + dt.timedelta(1)) and w['k'] == 1 and w['iso'] == iso(D0) and not w.get('cleared'), w
        assert await s.evaluate('dueAll().length') == 0, '틀린 날 바로 기한이 됨'
        await s.click('#bankNext'); await s.click('#bankQuit2'); await s.wait_for_timeout(200)
        # 다음 날: 기한 → 오늘 화면에 '오늘의 복습'
        await goto_day(s, D0 + dt.timedelta(1))
        assert await s.evaluate('dueAll().map(w => w.b)') == [qid], '문제 은행 오답이 다음 날 돌아오지 않음(!w.b 버그)'
        card = await s.locator('#revStart').inner_text(); assert '오늘의 복습' in card and '다시 볼 문제 1' in card, card
        await s.screenshot(path=f'{SC}/r01_today_review_light.png', full_page=True)
        await s.locator('.revcard').screenshot(path=f'{SC}/r01b_card_light.png')
        await s.locator('.rhythm.home').screenshot(path=f'{SC}/r01c_rhythm_light.png')

        # ───────── 2) 상자 오르기 · 기한 전에는 그대로 · 정리됨 규칙 ─────────
        await s.click('#revStart'); await s.wait_for_timeout(300)
        assert await s.evaluate('bs.kind') == 'review' and await s.evaluate('view') == 'bank'
        assert await s.evaluate("document.querySelector('.tab.on').dataset.v") == 'today', '오늘의 복습인데 문제 탭이 켜짐'
        n = await s.evaluate('bs.items.length')
        for i in range(n):
            mine = await s.evaluate('bs.recs[bs.i]') == 'b:' + qid
            await answer(s, True)
            if mine: assert '다음 복습은' in await s.locator('#v-bank .again').inner_text()
            await s.click('#bankNext'); await s.wait_for_timeout(120)
        assert '오늘의 복습을 마쳤습니다' in await s.locator('#v-bank').inner_text()
        assert await s.locator('.revnext').count() == 1, '끝나고 "다음 복습" 한 줄이 없음'
        await s.screenshot(path=f'{SC}/r02_review_done.png', full_page=True)
        w = await s.evaluate(f"findW({{ b:'{qid}' }})"); assert w['x'] == 2 and w['d'] == iso(D0 + dt.timedelta(4)), w
        await s.click('#bankQuit2'); await s.wait_for_timeout(200)
        assert '오늘의 복습을 마쳤습니다' in await s.locator('.revcard.done').inner_text(), '마친 뒤 오늘 화면 한 줄이 없음'
        # 기한 전(이틀 뒤)에 미리 맞힘 → 그대로
        await goto_day(s, D0 + dt.timedelta(2))
        r = await s.evaluate(f"srsMark({{ b:'{qid}' }}, true, 'O').st"); assert r == 'early'
        w = await s.evaluate(f"findW({{ b:'{qid}' }})"); assert w['x'] == 2 and w['d'] == iso(D0 + dt.timedelta(4)), '기한 전에 맞혔는데 상자가 움직임'
        # D0+4 (간격 3) → 상자 3, 7일 뒤
        await goto_day(s, D0 + dt.timedelta(4)); assert await s.evaluate(f"srsMark({{ b:'{qid}' }}, true, 'O').st") == 'up'
        w = await s.evaluate(f"findW({{ b:'{qid}' }})"); assert w['x'] == 3 and w['d'] == iso(D0 + dt.timedelta(11)) and not w.get('g'), w
        # D0+11 (간격 7) → 첫 번째 '7일 넘는' 정답: 아직 정리 아님, 상자 4, 14일 뒤
        await goto_day(s, D0 + dt.timedelta(11)); assert await s.evaluate(f"srsMark({{ b:'{qid}' }}, true, 'O').st") == 'up'
        w = await s.evaluate(f"findW({{ b:'{qid}' }})"); assert w['x'] == 4 and w['g'] == 1 and w['d'] == iso(D0 + dt.timedelta(25)) and not w.get('cleared'), w
        # D0+25 (간격 14) → 두 번째 잇단 정답 → 정리됨
        await goto_day(s, D0 + dt.timedelta(25)); assert await s.evaluate(f"srsMark({{ b:'{qid}' }}, true, 'O').st") == 'clear'
        assert await s.evaluate(f"findW({{ b:'{qid}' }}).cleared") is True

        # ───────── 3) 틀리면 상자 1로 · 정리 사슬이 끊긴다 ─────────
        D = D0 + dt.timedelta(26); await goto_day(s, D)
        q2 = await s.evaluate(f"BANK.find(q => q.lessonId === '{L1}' && q.type === 'ox' && q.id !== '{qid}').id")
        await s.evaluate(f"""(() => {{ S.wrong.push({{ b:'{q2}', p:'O', iso:'{iso(D - dt.timedelta(30))}', a:'{iso(D - dt.timedelta(7))}', d:'{iso(D)}', x:3, k:1, g:1 }}); save(S); }})()""")
        assert await s.evaluate(f"srsMark({{ b:'{q2}' }}, false, 'X').st") == 'reset'
        w = await s.evaluate(f"findW({{ b:'{q2}' }})"); assert w['x'] == 1 and w['k'] == 2 and w['d'] == iso(D + dt.timedelta(1)) and not w.get('g'), w
        assert w['iso'] == iso(D - dt.timedelta(30)), '처음 틀린 날이 바뀜'
        # 정리된 문제를 또 틀리면 다시 살아난다(기록 하나)
        assert await s.evaluate(f"srsMark({{ b:'{qid}' }}, false, 'X').st") == 'reset'
        assert await s.evaluate(f"S.wrong.filter(w => w.b === '{qid}').length") == 1 and await s.evaluate(f"!findW({{ b:'{qid}' }}).cleared")
        # 7일 안 되는 간격의 정답은 정리 사슬(g)을 이어 주지 않는다
        await s.evaluate(f"(() => {{ const w = findW({{ b:'{q2}' }}); Object.assign(w, {{ x:4, g:1, a:'{iso(D - dt.timedelta(3))}', d:'{iso(D)}' }}); }})()")
        assert await s.evaluate(f"srsMark({{ b:'{q2}' }}, true, 'O').st") == 'up' and not await s.evaluate(f"findW({{ b:'{q2}' }}).g"), '짧은 간격 정답이 정리 사슬을 이어 줌'

        # ───────── 4) 시험이 다가오면 간격을 줄인다(남은 날 × 20 %, 최소 1일) ─────────
        q3 = await s.evaluate(f"BANK.find(q => q.lessonId === '{L1}' && q.type === 'ox' && ![ '{qid}', '{q2}' ].includes(q.id)).id")
        seed3 = f"(() => {{ S.wrong = S.wrong.filter(w => w.b !== '{q3}'); S.wrong.push({{ b:'{q3}', p:'O', iso:'{iso(D - dt.timedelta(20))}', a:'{iso(D - dt.timedelta(7))}', d:'{iso(D)}', x:3, k:1 }}); }})()"
        await s.evaluate(seed3)
        await s.evaluate(f"S.sched.ddays = [{{ id:'ex1', title:'중간고사', date:'{iso(D + dt.timedelta(10))}' }}]; S.sched.events = []")
        assert await s.evaluate(f"examLeft('{L1}')") == 10
        await s.evaluate(f"srsMark({{ b:'{q3}' }}, true, 'O')")
        w = await s.evaluate(f"findW({{ b:'{q3}' }})"); assert w['x'] == 4 and w['d'] == iso(D + dt.timedelta(2)), f'D-10 인데 간격이 2일로 줄지 않음: {w}'
        # 시험 4일 전: 4×0.2 = 0.8 → 최소 1일
        await s.evaluate(f"S.sched.ddays = [{{ id:'ex1', title:'중간고사', date:'{iso(D + dt.timedelta(4))}' }}]"); await s.evaluate(seed3)
        await s.evaluate(f"srsMark({{ b:'{q3}' }}, true, 'O')"); assert await s.evaluate(f"findW({{ b:'{q3}' }}).d") == iso(D + dt.timedelta(1))
        # 다른 소단원 범위만 건 시험 일정은 이 문제의 간격을 줄이지 않는다
        other = await s.evaluate(f"LESSONS.find(l => l.id !== '{L1}').id")
        await s.evaluate(f"S.sched.ddays = []; S.sched.events = [{{ id:'ev1', title:'단원 평가', date:'{iso(D + dt.timedelta(10))}', kind:'exam', scope:{{ lesson:'{other}' }} }}]"); await s.evaluate(seed3)
        assert await s.evaluate(f"examLeft('{L1}')") is None
        await s.evaluate(f"srsMark({{ b:'{q3}' }}, true, 'O')"); assert await s.evaluate(f"findW({{ b:'{q3}' }}).d") == iso(D + dt.timedelta(14))
        await s.evaluate("S.sched.events = []; save(S)")

        # ───────── 5) 하루 10개까지 · 밀린 것부터 ─────────
        D = D0 + dt.timedelta(40); await goto_day(s, D)
        ids = await s.evaluate("BANK.filter(q => q.type === 'ox').slice(0, 15).map(q => q.id)")
        await s.evaluate(f"""(() => {{ S.wrong = {json.dumps(ids)}.map((id, i) => ({{ b:id, p:'O', iso:'2026-10-01', a:'2026-10-01', d:addDays('{iso(D)}', -15 + i), x:1, k:1 }})); S.rv = null; save(S); }})()""")
        assert await s.evaluate('dueAll().length') == 15 and await s.evaluate('dueToday().length') == 10, '하루 10개 상한이 없음'
        assert await s.evaluate('dueToday().map(w => w.b)') == ids[:10], '밀린 것부터 나오지 않음'
        for i in range(3): await s.evaluate(f"srsMark({{ b:'{ids[i]}' }}, true, 'O')")
        assert await s.evaluate('dueToday().length') == 7, await s.evaluate('dueToday().length')
        assert await s.evaluate('dueToday()[0].b') == ids[3]
        # 6번 넘게 틀린 문제 → 다시 묻지 않고 개념 카드로
        await s.evaluate(f"(() => {{ S.wrong = [{{ b:'{ids[0]}', p:'O', iso:'2026-10-01', a:'{iso(D - dt.timedelta(1))}', d:'{iso(D)}', x:1, k:6 }}]; S.rv = null; save(S); }})()")
        await s.evaluate("show('today')"); await s.wait_for_timeout(200); await s.click('#revStart'); await s.wait_for_timeout(300)
        while await s.evaluate("bs.recs[bs.i] !== 'b:" + ids[0] + "'"):
            await answer(s, True); await s.click('#bankNext'); await s.wait_for_timeout(100)
        assert await s.locator('.leechcard').count() == 1 and await s.locator('#v-bank .opts, #v-bank .oxrow').count() == 0, '여러 번 틀린 문제를 또 물음'
        assert '개념 카드부터 다시' in await s.locator('.leechcard').inner_text()
        await s.screenshot(path=f'{SC}/r03_leech.png', full_page=True)
        await s.click('.leechcard [data-leech]'); await s.wait_for_timeout(300)
        assert await s.evaluate('view') == 'detail', '개념 카드로 가지 않음'
        w = await s.evaluate(f"findW({{ b:'{ids[0]}' }})"); assert w.get('rd') == iso(D) and w['d'] == iso(D + dt.timedelta(1)), w
        # 오답 노트에서도: 다시 읽은 뒤엔 '지금 다시 풀기', 또 틀리면 다시 '개념 카드부터 다시'
        await s.evaluate(f"srsMark({{ b:'{ids[0]}' }}, false, 'X')"); await s.evaluate("show('wrong')"); await s.wait_for_timeout(300)
        assert await s.locator('#v-wrong [data-leech]').count() == 1 and '개념부터 다시' in await s.locator('#v-wrong').inner_text()
        await s.screenshot(path=f'{SC}/r04_wrong_note.png', full_page=True)

        # ───────── 6) 오늘의 복습 — 섞어 풀기 · 같은 소단원이 잇달아 나오지 않음 ─────────
        D = D0 + dt.timedelta(50); await goto_day(s, D)
        T = await s.evaluate('todayConcept().lessonId')
        ls = await s.evaluate(f"openLessons().map(l => l.id).filter(l => l !== '{T}').slice(0, 4)")
        A = ls[0]
        dueA = await s.evaluate(f"BANK.filter(q => q.lessonId === '{A}' && q.type === 'ox').slice(0, 3).map(q => q.id)")
        await s.evaluate(f"""(() => {{ S.wrong = {json.dumps(dueA)}.map((id, i) => ({{ b:id, p:'O', iso:'2026-10-01', a:'{iso(D - dt.timedelta(3))}', d:'{iso(D - dt.timedelta(3 - i))}', x:2, k:1 }}));
            S.done = CONCEPTS.filter(c => {json.dumps(ls)}.includes(c.lessonId) || c.lessonId === '{T}').map(c => c.id); S.bh = {{}}; S.rv = null; bs = null; save(S); }})()""")
        await s.evaluate("show('today')"); await s.wait_for_timeout(200)
        card = await s.locator('#revStart').inner_text(); assert '오늘의 복습' in card and '5' in card and '다시 볼 문제 3' in card and '지난 소단원 2' in card, card
        for _ in range(12):
            plan = await s.evaluate("reviewPlan(true).items.map(e => ({ l:e.lesson, due:!!e.w, q:(e.q||reviewItem(e.w)).lessonId }))")
            seq = [x['l'] for x in plan]
            assert len(plan) == 5 and sum(x['due'] for x in plan) == 3, plan
            assert all(seq[i] != seq[i+1] for i in range(4)), f'같은 소단원이 잇달아 나옴: {seq}'
            assert all(x['l'] == x['q'] for x in plan) and T not in [x['l'] for x in plan if not x['due']], plan
            assert len({x['l'] for x in plan if not x['due']}) == 2, '섞기 두 문제가 같은 소단원'
        await s.click('#revStart'); await s.wait_for_timeout(300)
        seq = await s.evaluate('bs.items.map(q => q.lessonId)'); assert len(seq) == 5 and all(seq[i] != seq[i+1] for i in range(4)), seq
        assert await s.locator('.qhead .rk').count() == 1
        await s.screenshot(path=f'{SC}/r05_review_session.png', full_page=True)
        # 문제 탭으로 가면 문제 은행 첫 화면, 오늘로 돌아오면 이어서 풀기
        await answer(s, True); await s.click('#bankNext'); await s.wait_for_timeout(100)
        await s.click('.tab[data-v="bank"]'); await s.wait_for_timeout(300); assert await s.locator('#bankStart').count() == 1, '문제 탭이 오늘의 복습에 묶임'
        await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(300); assert '이어서 풀기 · 1 / 5' in await s.locator('#revStart').inner_text()
        await s.click('#revStart'); await s.wait_for_timeout(200); assert await s.evaluate('bs.i') == 1
        # 다른 소단원이 없고 기한 문제가 모두 한 소단원이면 붙지 않게 1문제만
        await s.evaluate(f"(() => {{ bs = null; S.done = CONCEPTS.filter(c => c.lessonId === '{T}').map(c => c.id); S.bh = {{}}; S.rv = null; save(S); }})()")
        assert await s.evaluate("reviewPlan(true).items.length") == 1
        # 기한 문제도, 배운 다른 소단원도 없으면 카드를 숨긴다(기한 문제만 있으면 그것만)
        await s.evaluate("S.wrong = []; S.bh = {}; S.rv = null; save(S); show('today')"); await s.wait_for_timeout(200)
        assert await s.locator('.revcard').count() == 0, '복습할 것이 없는데 카드가 보임'

        # ───────── 7) 이번 주 리듬 — 점 7개, 연속 일수는 어디에도 없음 ─────────
        D = dt.date(2026, 12, 3)      # 목요일
        await goto_day(s, D)
        mon = D - dt.timedelta(D.weekday())
        studied = [mon, mon + dt.timedelta(1), D, mon - dt.timedelta(1), mon - dt.timedelta(2)]   # 이번 주 3일 + 지난 주말(연속처럼 보이는 날)
        await s.evaluate(f"S.days = {json.dumps(sorted(iso(x) for x in studied))}; save(S); show('today')"); await s.wait_for_timeout(300)
        rh = s.locator('.rhythm.home')
        assert await rh.locator('.dt').count() == 7 and await rh.locator('.dt.on').count() == 3 and await rh.locator('.dt.later').count() == 3, '이번 주 리듬 점이 맞지 않음'
        assert '3' in await rh.locator('.n').inner_text() and '이번 주 리듬' in await rh.inner_text()
        assert '7일 가운데 3일' in await rh.get_attribute('aria-label')
        assert not STREAK.search(await visible_text(s)), '오늘 화면에 연속 일수'
        await rh.screenshot(path=f'{SC}/r06_rhythm_light.png')
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300)
        assert '이번 주 3일' in await s.locator('#goStats').inner_text() and not STREAK.search(await visible_text(s)), '내 정보에 연속 일수'
        await s.click('#goStats'); await s.wait_for_timeout(500)
        t = await s.locator('.tiles').inner_text(); assert '이번 주 리듬' in t and not STREAK.search(await visible_text(s)), t
        await s.locator('.tiles').screenshot(path=f'{SC}/r07_stats_tiles_light.png')
        await s.evaluate('flushProgress()'); await s.wait_for_timeout(300)
        # 보호자 화면
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); await s.click('#logout'); await s.wait_for_timeout(500)
        await s.click('#goLogin'); await s.fill('#lgEmail', 'parent@demo.kr'); await s.fill('#lgPw', '1234'); await s.click('#lgGo'); await s.wait_for_timeout(1200)
        if await s.evaluate('view') != 'parent': await s.evaluate("show('parent')"); await s.wait_for_timeout(800)
        pw = await s.locator('.pweek').inner_text()
        assert '이번 주 리듬' in pw and '3/7일' in pw.replace('\n', ''), pw
        assert not STREAK.search(await visible_text(s)), '보호자 화면에 연속 일수'
        assert await s.locator('.pweek .week .d.later').count() == 3, '보호자 주간 띠가 이번 주(월–일)가 아님'
        await s.screenshot(path=f'{SC}/r08_parent_week.png', full_page=True)

        # ───────── 8) 옛 오답 기록 옮기기(날짜 보존 · 상자 1 · 문제 은행 오답도 다시 나옴) ─────────
        old = {'introSeen': True, 'onboarded': True, 'start': '2026-09-01', 'days': ['2026-09-20'], 'wrong': [
            {'l': '1101', 'n': 1, 'p': 2, 'iso': '2026-09-20', 'date': '9월 20일'},
            {'b': '1101-q7', 'p': '③', 'iso': '2026-09-25', 'date': '9월 25일'},
            {'l': '1101', 'n': 2, 'p': 1, 'iso': '2026-09-10', 'date': '9월 10일', 'redone': True, 'cleared': True},
            {'b': '1102-q4', 'p': '모름', 'iso': '2026-10-04', 'date': '10월 4일'}]}
        m = await page(init=f"localStorage.setItem('pcs.v2', {json.dumps(json.dumps(old, ensure_ascii=False))})")
        W = await m.evaluate('S.wrong')
        assert len(W) == 4, W
        assert W[0]['iso'] == '2026-09-20' and W[0]['date'] == '9월 20일' and W[0]['x'] == 1 and W[0]['d'] == '2026-09-21' and W[0]['k'] == 1 and W[0]['p'] == 2, W[0]
        assert W[1]['b'] == '1101-q7' and W[1]['iso'] == '2026-09-25' and W[1]['x'] == 1 and W[1]['d'] == '2026-09-26', W[1]
        assert W[2].get('cleared') is True and 'redone' not in W[2] and W[2]['iso'] == '2026-09-10', W[2]
        assert W[3]['d'] == '2026-10-05', W[3]
        assert await m.evaluate('dueAll().map(wKey)') == ['1101:1', 'b:1101-q7', 'b:1102-q4'], await m.evaluate('dueAll().map(wKey)')
        await m.wait_for_timeout(300); assert json.loads(await m.evaluate("localStorage.getItem('pcs.v2')"))['wrong'][0]['x'] == 1, '옮긴 기록이 기기에 저장되지 않음'
        await m.evaluate('loadMore()'); await m.wait_for_function('MORE.ok', timeout=15000)
        size = await m.evaluate("new TextEncoder().encode(JSON.stringify(Object.assign(snapshot(), { wrong: BANK.map(q => ({ b:q.id, p:'③', iso:'2026-10-01', a:'2026-10-01', d:'2026-10-02', x:3, k:2, g:1 })) }))).length")
        assert size < 250000, f'문제 은행 전부를 틀려도 진도 JSON 이 {size} 바이트 — 서버 한도(500,000)의 절반을 넘음'
        print('진도 JSON(문제 은행 전부 오답일 때):', size, '바이트')
        await m.context.close()

        # ───────── 9) 차분한 알림 — 3일 내리 열지 않으면 멈추고, 내 정보에 한 번만 ─────────
        STUB = """window.__ln = { sched: [], cancel: [] };
window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'android', Plugins: {
  LocalNotifications: { cancel: async (o) => { window.__ln.cancel.push(o); }, checkPermissions: async () => ({ display:'granted' }),
    requestPermissions: async () => ({ display:'granted' }), schedule: async (o) => { window.__ln.sched.push(o); return { notifications: o.notifications }; } } } };"""
        def seed(last, extra=None):
            st = {'introSeen': True, 'onboarded': True, 'start': '2026-09-01', 'notifyAt': '18:00', 'lastOpen': last, 'days': [],
                  'wrong': [{'b': '1101-q7', 'p': '③', 'iso': '2026-10-01', 'a': '2026-10-01', 'd': '2026-10-06', 'x': 2, 'k': 1}]}
            st.update(extra or {}); return f"if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded', 1); localStorage.setItem('pcs.v2', {json.dumps(json.dumps(st, ensure_ascii=False))}); }}"
        # (가) 이틀 전에 열었음(무반응 1일) → 계속 건다: 오늘 18시 + 앞으로 3일, 사실만 담은 문구
        n1 = await page(init=seed(iso(D0 - dt.timedelta(2))), stub=STUB)
        ln = await n1.evaluate('__ln'); assert ln['sched'], '알림을 걸지 않음'
        notes = ln['sched'][-1]['notifications']; assert len(notes) == 4 and [x['id'] for x in notes] == [1, 2, 3, 4], notes
        assert all(x.get('isExactNotification') is False for x in notes), '정확한 알람 권한 화면을 띄우는 설정'
        assert '다시 볼 문제 1개' in notes[2]['body'] and '오늘의 개념' in notes[0]['body'], [x['body'] for x in notes]
        assert await n1.evaluate('!S.nPause') and await n1.evaluate('S.lastOpen') == iso(D0)
        await n1.context.close()
        # (나) 4일 전에 마지막으로 열었음 → 그 사이 3일 알림을 모두 지나침 → 멈춤, 걸지 않음
        n2 = await page(init=seed(iso(D0 - dt.timedelta(4))), stub=STUB)
        ln = await n2.evaluate('__ln'); assert not ln['sched'] and ln['cancel'], f'3일 무반응인데 또 알림을 걸었음: {ln}'
        assert await n2.evaluate('S.nPause && S.nPause.d') == iso(D0)
        await n2.click('.tab[data-v="me"]'); await n2.wait_for_timeout(300)
        pn = n2.locator('.pausenote'); assert await pn.count() == 1 and '알림을 잠시 멈췄습니다' in await pn.inner_text() and '다시 켜기' in await pn.inner_text()
        box = await n2.locator('#notifyResume').bounding_box(); assert box['height'] >= 44, box
        await n2.screenshot(path=f'{SC}/r09_notify_paused.png', full_page=True)
        # 한 번만: 다시 켜면(앱을 다시 열면) 안내 카드는 없고 설정 줄의 작은 글씨만
        await n2.reload(); await n2.wait_for_timeout(600); await n2.click('.tab[data-v="me"]'); await n2.wait_for_timeout(300)
        assert await n2.locator('.pausenote').count() == 0, '멈춤 안내가 또 보임'
        assert '잠시 멈춤' in await n2.locator('#v-me').inner_text()
        assert not (await n2.evaluate('__ln'))['sched'], '멈춘 뒤 다시 열었는데 알림을 걸었음'
        await n2.context.close()
        # (다) 안내에서 '다시 켜기' → 다시 건다
        n3 = await page(init=seed(iso(D0 - dt.timedelta(5))), stub=STUB)
        await n3.click('.tab[data-v="me"]'); await n3.wait_for_timeout(300); await n3.click('#notifyResume'); await n3.wait_for_timeout(300)
        ln = await n3.evaluate('__ln'); assert ln['sched'] and len(ln['sched'][-1]['notifications']) >= 3, ln
        assert await n3.evaluate('!S.nPause') and await n3.locator('.pausenote').count() == 0
        await n3.context.close()

        # ───────── 10) 어두운 화면 스크린샷(오늘의 복습 카드 · 이번 주 리듬) ─────────
        dk = {'introSeen': True, 'onboarded': True, 'start': iso(D0 + dt.timedelta(2)), 'days': [iso(D0 - dt.timedelta(1)), iso(D0)],
              'done': [], 'wrong': [{'l': '1101', 'n': 1, 'p': 2, 'iso': '2026-10-01', 'a': '2026-10-01', 'd': iso(D0), 'x': 1, 'k': 1}]}
        for color in ('light', 'dark'):
            d = await page(color=color, init=f"localStorage.setItem('pcs.v2', {json.dumps(json.dumps(dk, ensure_ascii=False))})", when=D0 + dt.timedelta(2))
            await d.evaluate("S.days.push(todayISO()); S.done = CONCEPTS.slice(0, 7).map(c => c.id); save(S); show('today')"); await d.wait_for_timeout(400)
            assert await d.locator('#revStart').count() == 1
            await d.screenshot(path=f'{SC}/r10_today_{color}.png')
            await d.locator('.revcard').screenshot(path=f'{SC}/r10b_card_{color}.png')
            await d.locator('.rhythm.home').screenshot(path=f'{SC}/r10c_rhythm_{color}.png')
            await d.context.close()

        bad = [e for e in errs if 'favicon' not in e]
        assert not bad, bad
        print('REVIEW E2E OK · 콘솔 오류', bad)


asyncio.run(main())
