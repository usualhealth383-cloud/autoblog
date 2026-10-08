#!/usr/bin/env python3
"""7일 사용 E2E(2026-10-07 실제 사용자처럼 일주일 써 보기 점검에서 나온 핵심 단언) — 로컬 모드, 고정 시계로 하루씩 넘긴다.

새 학생(월요일 처음 설치 → 소개 → 학원 코드로 가입 → 매일 홈 '하루 경로')
· 개념 읽기 → '공부했음' 뒤 주 버튼은 경로의 다음 단계('오늘 할 일로 · 다음은 빈칸 떠올리기') — 소단원 54문항으로 빠지지 않음
· 홈 '오늘의 복습 n' = 줄 글(다시 볼 문제·개념 카드·지난 소단원) 합 = 실제로 나오는 문항 수
· 첫 주(배운 소단원이 하나뿐)에도 세트가 1문제씩 쪼개지지 않고, 개념 카드가 실제로 나온다(전엔 맨 뒤로 밀려 한 번도 안 나옴)
· 세트를 마쳤는데 오늘 몫이 남으면 '한 묶음을 마쳤어요' + '이어서 복습하기', 다 마치면 '오늘의 복습을 마쳤어요'
· 다 끝낸 날 '다음 복습은 …'은 한 번만(복습 줄과 끝 카드에 두 번 나오던 것)
· 알림이 셀 '다시 볼 것' = 오늘 기한 문제 + 개념 카드(remindDue — 문제만 세던 것)
· 노트 한 줄: 홈 카드 안내는 '하나만'(쓰기 기본이 한 칸인데 '세 줄로'라 하던 것) · 한 줄 노트 카드에 번호 '1' 없음
· 앱을 켜 둔 채 자정을 넘기면(첫 1분 안이어도) 새 날 경로로 다시 그림
· 5일째(금) 빼먹음 → 7일째(일) '이번 주 리듬' 7일 가운데 6일 · 다음 주 월요일 0일
· 오늘의 문제 오답 문구 '②예요'(받침 없는 번호) · 날마다 가로 넘침 없음 · 콘솔 오류 없음
보호자(같은 기기 로컬 DB): 연결 요청 중에는 '다른 자녀도 연결하기' · 확인 뒤 이번 주 요약 = 학생 기록(공부한 날·개념) · 수업 없는 요일은 '수업 없는 날'
원장: 할 일이 없으면 '처리할 것' 설명은 한 줄 · 과제(5문제) → 학생 카드 0/5 → 풀면 제출 현황 1/1·5문항

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_week.py [--shots 폴더]
"""
import asyncio, sys, os, re, datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import auto_yes, signup, approve_child
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_week'; os.makedirs(SC, exist_ok=True)
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 12)   # 월요일


def at(n, hh=19, mm=0):
    d = D0 + dt.timedelta(n - 1); return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=KST)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844})
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
        await pg.clock.set_fixed_time(at(1, 18)); await auto_yes(pg)
        await pg.goto(APP); await pg.wait_for_timeout(800)

        async def tidy(where):
            r = await pg.evaluate("({ sw:document.scrollingElement.scrollWidth, vw:innerWidth })"); assert r['sw'] <= r['vw'], (where, r)

        async def home():
            return await pg.evaluate("""(() => ({ now:(document.querySelector('#v-today .ps.now')||{}).id || '', date:(document.querySelector('#v-today .hello small')||{}).textContent || '',
              rev:(document.querySelector('#ps-review')||{}).innerText || '' }))()""")

        async def day(n, hh=19):
            await pg.clock.set_fixed_time(at(n, hh)); await pg.reload(); await pg.wait_for_timeout(900)
            await pg.evaluate('loadMore()'); await pg.wait_for_function('MORE.ok', timeout=15000)
            assert await pg.evaluate('todayISO()') == (D0 + dt.timedelta(n - 1)).isoformat()
            assert await pg.evaluate('view') == 'today', await pg.evaluate('view')

        async def answer(ok):
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer, n:(q.choices||[]).length }; })()")
            if q['t'] == 'card':
                await pg.click('#csFlip'); await pg.wait_for_timeout(80); await pg.click(f'[data-csr="{"o" if ok else "x"}"]')
            elif q['t'] == 'ox': await pg.click(f'[data-ox="{q["a"] if ok else ("X" if q["a"] == "O" else "O")}"]')
            elif q['t'] == 'blank': await pg.fill('#blankIn', str(q['a']) if ok else '모름'); await pg.click('#blankGo')
            elif q['t'] == 'essay': await pg.click('#essayShow'); await pg.wait_for_timeout(80); await pg.click('[data-ess="맞음"]')
            else: await pg.click(f'[data-bp="{q["a"] if ok else (q["a"] % q["n"]) + 1}"]')
            await pg.wait_for_timeout(150)

        async def path(n, quiz_ok=True, rev_ok=lambda i: True):
            assert (await home())['now'] == 'ps-read'
            await pg.click('#pRead'); await pg.wait_for_timeout(300); await pg.click('#markDone'); await pg.wait_for_timeout(250)
            go = await pg.inner_text('#dPathGo'); assert '오늘 할 일로' in go and '빈칸 떠올리기' in go, ('공부했음 뒤 주 버튼이 경로 다음 단계가 아님', go)
            assert await pg.locator('#v-detail .dact > .btn[data-drill]').count() == 0
            await pg.click('#dPathGo'); await pg.wait_for_timeout(300); assert (await home())['now'] == 'ps-blank'
            await pg.click('#pBlank'); await pg.wait_for_timeout(200); await pg.click('#bkGo'); await pg.wait_for_timeout(150); await pg.click('#bkDone'); await pg.wait_for_timeout(200)
            await pg.click('#goQuiz'); await pg.wait_for_timeout(250); a = await pg.evaluate('qState.q.answer')
            await pg.click(f'.opt[data-p="{a if quiz_ok else (1 if a != 1 else 2)}"]'); await pg.wait_for_timeout(250)
            if not quiz_ok:
                v = await pg.inner_text('#v-quiz .verdict'); m = re.search(r'정답은 (.)(이에요|예요)', v); assert m, v
                assert m.group(2) == ('예요' if a in (2, 4, 5) else '이에요'), ('번호 뒤 이에요/예요', v)
            await pg.click('#grade'); await pg.wait_for_timeout(300)
            sets = 0
            while (await home())['now'] == 'ps-review':
                h = (await home())['rev']; m = re.search(r'오늘의 복습 (\d+)', h); assert m, h
                parts = [int(x) for x in re.findall(r'(?:다시 볼 문제|개념 카드|지난 소단원) (\d+)', h)]
                assert sum(parts) == int(m.group(1)), ('홈 복습 수와 줄 글 합이 다름', h)
                await pg.click('#revStart'); await pg.wait_for_timeout(300)
                items = await pg.evaluate('bs.items.map(q => q.type)'); assert len(items) == int(m.group(1)), ('홈 복습 수와 실제 문항 수가 다름', h, items)
                if 'card' not in items: assert not await pg.evaluate("bs.items.length && csToday().length"), '오늘 카드가 있는데 세트에 없음'
                i = 0
                while await pg.evaluate('!!(bs && bs.items[bs.i])'):
                    await answer(rev_ok(i)); await pg.click('#bankNext'); await pg.wait_for_timeout(150); i += 1
                res = await pg.inner_text('#v-bank'); more = await pg.evaluate('reviewPlan(false).items.length')
                if more: assert '한 묶음을 마쳤어요' in res and await pg.locator('#revMore').count() == 1 and await pg.locator('#bankQuit2').count() == 1, res
                else: assert '오늘의 복습을 마쳤어요' in res and await pg.locator('#revMore').count() == 0, res
                await pg.click('#bankQuit2'); await pg.wait_for_timeout(300); sets += 1; assert sets <= 4, '복습 세트가 끝나지 않음'
            assert (await home())['now'] == 'ps-fin'
            t = await pg.inner_text('#v-today'); assert t.count('다음 복습은') <= 1, ('같은 말 두 번', t[:400])
            await tidy(f'{n}일째 끝')
            return sets

        # ───── 1일째(월): 처음 설치 → 소개 → 가입 ─────
        for i in range(3): await pg.click('#introNext'); await pg.wait_for_timeout(200)
        await signup(pg, '하늘', 'sky@week.kr', code='MON123')
        assert await pg.evaluate('view') == 'today'
        await pg.evaluate('loadMore()'); await pg.wait_for_function('MORE.ok', timeout=15000)
        r = await pg.inner_text('#ps-review'); assert '오늘 다시 볼 것 없음' in r, r
        assert '하나만' in await pg.inner_text('#goNote'), '노트 카드 안내가 쓰기 화면(한 칸)과 다름'
        await pg.screenshot(path=f'{SC}/w01_day1_home.png')
        await path(1)
        await pg.click('#goNote'); await pg.wait_for_timeout(300); await pg.click('#noteNew'); await pg.wait_for_timeout(300)
        await pg.fill('#nedF0', '모든 사건은 시간과 공간 좌표로 적는다.'); await pg.wait_for_timeout(600); await pg.click('#nedDone'); await pg.wait_for_timeout(400)
        assert await pg.locator('#v-note .ncard.t-line3 .nl i').count() == 0, '한 줄 노트에 번호 1'
        await pg.evaluate("show('today')"); await pg.wait_for_timeout(250); assert '모든 사건은' in await pg.inner_text('#goNote')
        await pg.screenshot(path=f'{SC}/w02_day1_fin.png')

        # ───── 2~4일: 가끔 틀림 · 알림 수 · 첫 주 복습 세트 ─────
        await day(2)
        assert await pg.evaluate('remindDue(todayISO())') == await pg.evaluate('dueToday().length + csToday().length') >= 1
        await path(2, quiz_ok=False)
        await day(3)
        assert await pg.evaluate("remindDue(todayISO())") == await pg.evaluate('dueToday().length + csToday().length')
        assert await pg.evaluate("csToday().length") >= 1 and await pg.evaluate("reviewPlan(false).items.filter(e => e.cs).length") == await pg.evaluate("csToday().length"), '개념 카드가 오늘의 복습에서 빠짐'
        await pg.screenshot(path=f'{SC}/w03_day3_home.png')
        await path(3, rev_ok=lambda i: i != 0)
        # 앱을 켜 둔 채 자정을 넘김(연 지 1분이 안 됐어도)
        await pg.clock.set_fixed_time(at(3, 23, 59)); await pg.reload(); await pg.wait_for_timeout(600)
        await pg.clock.set_fixed_time(at(4, 0, 0) + dt.timedelta(seconds=20)); await pg.evaluate('dayRoll()'); await pg.wait_for_timeout(300)
        h = await home(); assert '15일' in h['date'] and h['now'] == 'ps-read', ('자정 넘긴 뒤 어제 경로가 남음', h)
        await day(4); await path(4, quiz_ok=False)
        # ───── 5일째 빼먹음 · 6·7일 ─────
        await day(6); await path(6, rev_ok=lambda i: i % 2 == 0)
        await day(7); await path(7)
        lab = await pg.get_attribute('#v-today .rhythm', 'aria-label'); assert '7일 가운데 6일' in lab and '금' not in lab, lab
        await pg.screenshot(path=f'{SC}/w04_day7_fin.png', full_page=True)
        n_days = await pg.evaluate('S.days.length'); n_done = await pg.evaluate('S.done.length')
        assert n_days == 6 and n_done == 6, (n_days, n_done)
        await pg.evaluate('flushProgress()'); await pg.wait_for_timeout(300)

        # ───── 보호자(같은 기기 · 로컬 DB) ─────
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(600)
        await pg.evaluate("authMode = 'start'; show('auth')"); await pg.wait_for_timeout(200)
        await signup(pg, '김보호', 'mom@week.kr', role='parent', child='MON123')
        t = await pg.inner_text('#v-parent'); assert '원장님 확인을 기다리고' in t and '다른 자녀도 연결하기' in t, t[:300]
        await approve_child(pg, 'MON123')
        ws = await pg.inner_text('#weekSum'); assert re.search(r'6\s*/7일', ws) and re.search(r'6\s*개\s*공부한 개념', ws), ws[:300]
        assert '수업 없는 날' in await pg.inner_text('#v-parent .pass'), '월목반인데 일요일에 아직 출석 전'
        await pg.screenshot(path=f'{SC}/w05_parent_week.png', full_page=True)
        await pg.clock.set_fixed_time(at(8, 19)); await pg.reload(); await pg.wait_for_timeout(900)
        assert '아직 출석 전' in await pg.inner_text('#v-parent .pass'), '월요일(수업 날)인데 수업 없는 날'

        # ───── 원장: 처리할 것 · 과제 → 학생 → 제출 현황 ─────
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(600)
        await pg.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await pg.wait_for_timeout(200)
        await pg.fill('#lgEmail', 'owner@parkchan.kr'); await pg.fill('#lgPw', '2580'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
        await pg.wait_for_selector('#todoBox')
        if await pg.locator('#todoBox .todo-row').count() == 0: assert '모읍니다' in await pg.inner_text('#todoBox') and len(await pg.inner_text('#todoBox .tip')) < 60
        await pg.click('[data-adm="asg"]'); await pg.wait_for_selector('#asgForm'); await pg.wait_for_function('MORE.ok', timeout=20000); await pg.wait_for_timeout(300)
        await pg.click('#asgForm [data-af="kind"][data-val="bank"]'); await pg.select_option('#afLesson', '1101'); await pg.click('#asgForm [data-af="n"][data-val="5"]')
        await pg.select_option('#afCls', '월목반'); await pg.wait_for_timeout(150)
        assert '문제 5개' in await pg.inner_text('#afSum'); await pg.click('#afSend'); await pg.wait_for_timeout(900)
        aid = await pg.evaluate("(async () => (await DBX.assignList()).find(a => a.title.includes('문제 5개')))()")
        assert aid and aid['n'] == 5, ('제목은 5개인데 문항 수가 다름', aid)
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(600)
        await pg.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await pg.wait_for_timeout(200)
        await pg.fill('#lgEmail', 'sky@week.kr'); await pg.fill('#lgPw', 'pass1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
        await pg.wait_for_selector('.asgcard'); card = pg.locator('.asgcard', has_text='문제 5개'); assert '0/5' in await card.inner_text()
        await card.click(); await pg.wait_for_timeout(500); assert await pg.evaluate('bs.items.length') == 5
        while await pg.evaluate('!!(bs && bs.items[bs.i])'):
            await answer(True); await pg.click('#bankNext'); await pg.wait_for_timeout(150)
        assert '학원에 냈어요' in await pg.inner_text('#v-bank')
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(300)
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(600)
        await pg.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await pg.wait_for_timeout(200)
        await pg.fill('#lgEmail', 'owner@parkchan.kr'); await pg.fill('#lgPw', '2580'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
        await pg.click('[data-adm="asg"]'); await pg.wait_for_timeout(700)
        await pg.locator(f'[data-asgrep="{aid["id"]}"]').click(); await pg.wait_for_timeout(600)
        rep = await pg.inner_text('.sheet'); assert '5문항' in rep and '5/5' in rep and '1/2' in rep, rep[:300]
        await pg.screenshot(path=f'{SC}/w06_owner_report.png')

        assert not errs, errs
        print('WEEK E2E OK · 콘솔 오류', errs)
        await b.close()


asyncio.run(main())
