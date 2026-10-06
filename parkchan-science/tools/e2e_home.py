#!/usr/bin/env python3
"""오늘(홈) — 하루 경로 E2E(홈 시안 C, 원장님 결정 2026-10-06).

개념 읽기 → 빈칸 ㉠㉡㉢ → 오늘의 문제 → 다시 볼 문제. 지금 단계만 큰 카드(화면당 하나), 끝낸 단계는 접힘, 아직은 작게.
· 손님: 네 단계 · 지금 = 개념 읽기 · 다시 볼 문제 없음(할 일로 세지 않음) · '둘러보는 중' 한 줄
· 상태 전이: 상세를 '포인트'까지 읽으면 읽기 끝(S.read) → 다음 카드가 펼쳐짐(줄임 설정이면 움직임 없음)
  → 빈칸 시트(문장마다 칸, 채점 S.tp.b) → 오늘의 문제(S.tp.q, 다시 열면 채점된 화면 그대로·두 번 세지 않음) → 다 끝냄 카드
· 복습 있음: 지금 = 오늘의 복습(규칙 한 문장) → 다 풀면 접힘 · 다음 날이면 새 경로
· 동기화: 진도 스냅숏에 tp·read · 다른 기기의 같은 날 기록을 합친다
· 과제 있음(원장이 낸 과제 카드가 경로 위) · 무료 범위(코드 없는 학생) 한 줄
· 발문 고딕 16px · 선지가 발문보다 작지 않음 · 홈에 명조는 한 마디 하나 · 가로 넘침·말줄임 없음 · 밝은/어두운 스크린샷

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_home.py [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes, signup
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_home'; os.makedirs(SC, exist_ok=True)
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 6)


def at(day, hh=12):
    return dt.datetime(day.year, day.month, day.day, hh, 0, tzinfo=KST)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []

        async def page(color='light', motion='no-preference'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color, reduced_motion=motion)
            await ctx.add_init_script(NO_INTRO)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await pg.clock.set_fixed_time(at(D0))
            await auto_yes(pg)
            await pg.goto(APP); await pg.wait_for_timeout(700)
            return pg

        async def state(pg):
            return await pg.evaluate("""(() => ({ now:(document.querySelector('#v-today .ps.now')||{}).id || '',
              cls:Object.fromEntries([...document.querySelectorAll('#v-today .ps')].map(e => [e.id, e.className.replace('ps','').trim()])),
              heroes:document.querySelectorAll('#v-today .pnow').length, head:(document.querySelector('#v-today .phead .n')||{}).textContent || '' }))()""")

        async def tidy(pg, where):
            """가로 넘침·말줄임·글자 잘림 없음"""
            r = await pg.evaluate("""(() => ({ sw:document.scrollingElement.scrollWidth, vw:innerWidth,
              ell:[...document.querySelectorAll('#v-today *')].filter(e => getComputedStyle(e).textOverflow === 'ellipsis' && e.offsetParent).map(e => e.className),
              cut:[...document.querySelectorAll('#v-today .pc, #v-today .pnow, #v-today .hrow')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.id || e.className) }))()""")
            assert r['sw'] <= r['vw'] and not r['ell'] and not r['cut'], (where, r)

        # ───────── 1) 손님 — 첫 화면 ─────────
        g = await page()
        await g.click('#goGuest'); await g.wait_for_timeout(400)
        st = await state(g)
        assert st['now'] == 'ps-read' and st['heroes'] == 1, st
        assert st['cls'] == {'ps-read': 'now', 'ps-blank': 'todo', 'ps-quiz': 'todo', 'ps-review': 'none'}, st
        assert st['head'] == '0 / 3', '다시 볼 문제가 없으면 할 일은 3개'
        assert await g.locator('#ps-read #pRead').count() == 1 and await g.locator('#goQuiz').count() == 1 and await g.locator('#revStart').count() == 0
        t = await g.inner_text('#v-today')
        assert '둘러보는 중이에요' in t and await g.evaluate("todayConcept().title") in await g.inner_text('#ps-read'), t[:300]
        assert '빈칸을 누르면' not in t and await g.locator('#v-today .prose').count() == 0, '개념 본문이 홈에 남아 있음'
        serif = await g.evaluate("[...document.querySelectorAll('#v-today *')].filter(e => e.offsetParent && e.childNodes.length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && getComputedStyle(e).fontFamily.includes('Serif')).map(e => e.tagName + '.' + e.className)")
        assert serif and all(x.startswith('BLOCKQUOTE') for x in serif), f'홈의 명조는 한 마디 하나: {serif}'
        hs = await g.evaluate("[...document.querySelectorAll('#v-today .pc')].map(e => e.getBoundingClientRect().height)"); assert min(hs) >= 44, hs
        await tidy(g, '손님')
        await g.screenshot(path=f'{SC}/h01_guest_light.png'); await g.screenshot(path=f'{SC}/h01b_guest_full_light.png', full_page=True)

        # ───────── 2) 읽기 → 빈칸 → 문제 → 다 끝냄 ─────────
        await g.click('#pRead'); await g.wait_for_timeout(400)
        assert await g.evaluate('view') == 'detail' and await g.evaluate('detailIdx === dayIndex()'), '읽기 단계가 오늘 개념 상세로 가지 않음'
        assert await g.evaluate('S.read.length') == 0, '열기만 했는데 읽음'
        await g.evaluate("document.querySelector('#v-detail .point').scrollIntoView({ block:'center' })"); await g.wait_for_timeout(500)
        assert await g.evaluate('S.read.includes(todayConcept().id)'), '포인트까지 내려 읽었는데 읽기 끝이 아님'
        await g.click('#backList'); await g.wait_for_timeout(120)
        st = await state(g); assert st['now'] == 'ps-blank' and st['cls']['ps-read'] == 'done' and st['head'] == '1 / 3', st
        assert await g.locator('#ps-blank.unfold').count() == 1, '다음 단계가 펼쳐지지 않음'
        await g.wait_for_timeout(500); assert await g.locator('.ps.unfold').count() == 0, '움직임이 끝나도 클래스가 남음'
        assert '다 읽었어요' in await g.inner_text('#ps-read')
        await g.screenshot(path=f'{SC}/h02_after_read_light.png')
        # 빈칸 시트
        await g.click('#pBlank'); await g.wait_for_timeout(300)
        items = await g.evaluate("blankItems(todayConcept())")
        assert len(items) == 3 and await g.locator('.bkl li').count() == 3 and await g.locator('.bkl .bkx').count() >= 3
        assert all('{{' + it['k'] + '}}' in it['s'] for it in items), items
        bad = await g.evaluate("CONCEPTS.filter(c => { const it = blankItems(c); return it.length !== 3 || it.some(x => !x.s.includes('{{' + x.k + '}}') || plain(x.s).length < 20); }).map(c => c.id)")
        assert not bad, f'빈칸 문장을 못 꺼낸 개념: {bad}'
        assert await g.evaluate("document.activeElement.id") == 'bk0'
        await g.fill('#bk0', items[0]['a']); await g.press('#bk0', 'Enter'); assert await g.evaluate("document.activeElement.id") == 'bk1', 'Enter 로 다음 칸에 가지 않음'
        await g.fill('#bk1', '모르겠음')
        await g.screenshot(path=f'{SC}/h03_blank_sheet_light.png')
        await g.click('#bkGo'); await g.wait_for_timeout(250)
        assert await g.evaluate('S.tp.b') == [1, 0, 0], await g.evaluate('S.tp')
        assert await g.locator('.bkr.ok').count() == 1 and await g.locator('.bkr.no').count() == 2 and items[1]['a'] in await g.inner_text('.bkl')
        await g.screenshot(path=f'{SC}/h04_blank_result_light.png')
        await g.click('#bkDone'); await g.wait_for_timeout(150)
        st = await state(g); assert st['now'] == 'ps-quiz' and st['cls']['ps-blank'] == 'done', st
        assert '3칸 가운데 1칸 맞혔어요' in await g.inner_text('#ps-blank')
        assert await g.evaluate("document.activeElement.id") == 'goQuiz', '빈칸을 마친 뒤 초점이 다음 단계로 가지 않음'
        # 오늘의 문제 — 발문 고딕 16px · 선지 ≥ 발문
        await g.click('#goQuiz'); await g.wait_for_timeout(300)
        f = await g.evaluate("(() => { const s = getComputedStyle(document.querySelector('#v-quiz .stem')), o = getComputedStyle(document.querySelector('#v-quiz .opt')); return { ff:s.fontFamily, fs:parseFloat(s.fontSize), of:parseFloat(o.fontSize) }; })()")
        assert 'Serif' not in f['ff'] and f['fs'] == 16 and f['of'] >= f['fs'], f
        await g.screenshot(path=f'{SC}/h05_quiz_light.png')
        ans = await g.evaluate('qState.q.answer'); await g.click(f'.opt[data-p="{ans}"]'); await g.wait_for_timeout(200)
        assert '맞았어요' in await g.inner_text('#v-quiz .verdict')
        assert await g.evaluate('S.tp.q') == 'o' and await g.evaluate('S.tp.qp') == ans
        a1 = await g.evaluate('S.stats.a')
        await g.click('#grade'); await g.wait_for_timeout(150)
        st = await state(g); assert st['now'] == 'ps-fin' and st['heroes'] == 1 and st['head'] == '3 / 3', st
        fin = await g.inner_text('#ps-fin'); assert '오늘 할 일 끝 — 내일 만나요' in fin and '내일의 개념' in fin, fin
        assert '맞았어요' in await g.inner_text('#ps-quiz')
        await tidy(g, '다 끝냄')
        await g.screenshot(path=f'{SC}/h06_fin_light.png'); await g.screenshot(path=f'{SC}/h06b_fin_full_light.png', full_page=True)
        # 다 푼 오늘의 문제를 다시 열면 채점된 화면 그대로(다시 세지 않음)
        await g.click('#goQuiz'); await g.wait_for_timeout(200)
        assert await g.locator('#v-quiz .verdict').count() == 1 and await g.locator('#v-quiz .opt:not([disabled])').count() == 0
        assert await g.evaluate('S.stats.a') == a1, '다시 열었더니 한 번 더 셈'
        await g.click('#grade'); await g.wait_for_timeout(150)

        # ───────── 3) 복습 있음 → 지금 단계 = 오늘의 복습 → 마치면 접힘 ─────────
        await g.evaluate("loadMore()"); await g.wait_for_function('MORE.ok', timeout=15000)
        await g.evaluate("""(() => { const q = BANK.find(x => x.lessonId === todayConcept().lessonId && x.type === 'ox');
          S.wrong = [{ b:q.id, p:'O', iso:addDays(todayISO(), -1), a:addDays(todayISO(), -1), d:todayISO(), x:1, k:1 }]; S.rv = null; save(S); show('today'); })()""")
        await g.wait_for_timeout(250)
        st = await state(g); assert st['now'] == 'ps-review' and st['head'] == '3 / 4', st
        rv = await g.inner_text('#ps-review'); assert '오늘의 복습 1' in rv and '다시 볼 문제 1' in rv and await g.evaluate('SRS_RULE') in rv, rv
        assert await g.locator('#ps-review #revStart').count() == 1
        await g.screenshot(path=f'{SC}/h07_review_now_light.png')
        await g.click('#revStart'); await g.wait_for_timeout(300); assert await g.evaluate("bs.kind") == 'review'
        q = await g.evaluate("bs.items[0].answer"); await g.click(f'[data-ox="{q}"]'); await g.wait_for_timeout(150)
        await g.click('#bankNext'); await g.wait_for_timeout(150); assert '오늘의 복습을 마쳤어요' in await g.inner_text('#v-bank')
        await g.click('#bankQuit2'); await g.wait_for_timeout(200)
        st = await state(g); assert st['now'] == 'ps-fin' and st['cls']['ps-review'] == 'done' and st['head'] == '4 / 4', st
        assert '오늘의 복습을 마쳤어요' in await g.inner_text('#ps-review')
        # 동기화: 스냅숏에 오늘 할 일·읽은 개념 · 같은 날 다른 기기 기록 합치기
        snap = await g.evaluate('snapshot()'); assert snap['tp']['b'] == [1, 0, 0] and snap['tp']['q'] == 'o' and snap['read'], snap['tp']
        # ───────── 4) 다음 날 — 새 경로(움직임 없음) · 다른 기기에서 빈칸을 끝냈으면 합쳐 보인다 ─────────
        await g.clock.set_fixed_time(at(D0 + dt.timedelta(1)))
        await g.evaluate("dayRoll(); show('today')"); await g.wait_for_timeout(200)
        st = await state(g); assert st['now'] == 'ps-read' and st['cls']['ps-blank'] == 'todo', st
        assert await g.locator('.ps.unfold').count() == 0, '날이 바뀌어 처음으로 돌아갔는데 펼침 움직임'
        await g.evaluate("mergeProgress({ tp:{ d:todayISO(), c:todayConcept().id, b:[1,1,1] }, read:[todayConcept().id], at:new Date(Date.now() + 1000).toISOString() }); show('today')"); await g.wait_for_timeout(200)
        st = await state(g); assert st['now'] == 'ps-quiz' and st['cls']['ps-read'] == 'done' and st['cls']['ps-blank'] == 'done', ('다른 기기 기록이 합쳐지지 않음', st)
        await g.evaluate("mergeProgress({ tp:{ d:addDays(todayISO(), -1), c:'x', q:'x' }, at:new Date(Date.now() + 2000).toISOString() }); show('today')"); await g.wait_for_timeout(150)
        assert await g.evaluate('S.tp.b') == [1, 1, 1] and not await g.evaluate('S.tp.q'), '어제 기록이 오늘을 덮음'
        await g.context.close()

        # ───────── 5) 줄임 설정: 펼침 움직임 없음 ─────────
        r = await page(motion='reduce')
        await r.click('#goGuest'); await r.wait_for_timeout(300)
        await r.evaluate("markRead(todayConcept().id); save(S)"); await r.click('#pRead'); await r.wait_for_timeout(200); await r.click('#backList'); await r.wait_for_timeout(100)
        assert await r.locator('.ps.unfold').count() == 0 and (await state(r))['now'] == 'ps-blank'
        await r.context.close()

        # ───────── 6) 과제 있음(경로 위 카드) · 무료 범위 한 줄 ─────────
        s = await page()
        await s.click('#goLogin'); await s.click('[data-demo^="owner"]'); await s.click('#lgGo'); await s.wait_for_timeout(1000)
        await s.evaluate("(async () => { const L = LESSONS[0].id; const ids = BANK.length ? [] : []; await loadMore(); const items = BANK.filter(q => q.lessonId === L && q.type === 'ox').slice(0, 3).map(q => q.id); await DBX.assignCreate({ kind:'bank', title:'과제 시험 OX', ref:L, items, cls:'월목반', due:addDays(todayISO(), 2) }); })()")
        await s.wait_for_timeout(600)
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#logout'); await s.wait_for_timeout(600)
        await s.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await s.wait_for_timeout(200)
        await s.click('[data-demo^="student"]'); await s.click('#lgGo'); await s.wait_for_selector('.asgcard', timeout=8000)
        order = await s.evaluate("(() => { const a = document.querySelector('.asgcard'), p = document.querySelector('#v-today .path'); return !!(a && p && (a.compareDocumentPosition(p) & 4)); })()")
        assert order, '과제 카드가 경로 위에 있지 않음'
        st = await state(s); assert st['heroes'] == 1, st
        assert await s.locator('#v-today .pfoot').count() == 0, '전 범위 학생에게 무료 범위 안내'
        await tidy(s, '과제')
        await s.screenshot(path=f'{SC}/h08_assign_light.png')
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#logout'); await s.wait_for_timeout(600)
        await s.evaluate("authMode = 'start'; show('auth')"); await s.wait_for_timeout(200)
        await signup(s, '무료학생', 'free@home.kr')
        assert await s.evaluate('view') == 'today' and not await s.evaluate('fullAccess()')
        assert '최근 7일치 개념이 열려 있어요' in await s.inner_text('#v-today .pfoot')
        await s.click('#pfootGo'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'plans'
        await s.context.close()

        # ───────── 7) 어두운 화면 — 같은 흐름 스크린샷 ─────────
        d = await page('dark')
        await d.click('#goGuest'); await d.wait_for_timeout(400)
        await d.screenshot(path=f'{SC}/h11_guest_dark.png')
        await d.evaluate("markRead(todayConcept().id); save(S); show('today')"); await d.wait_for_timeout(200)
        await d.click('#pBlank'); await d.wait_for_timeout(200); await d.click('#bkGo'); await d.wait_for_timeout(200)
        await d.screenshot(path=f'{SC}/h12_blank_result_dark.png')
        await d.click('#bkDone'); await d.wait_for_timeout(200); await d.screenshot(path=f'{SC}/h13_quiz_now_dark.png')
        await d.click('#goQuiz'); await d.wait_for_timeout(200); ans = await d.evaluate('qState.q.answer')
        await d.click(f'.opt[data-p="{1 if ans != 1 else 2}"]'); await d.wait_for_timeout(200); await d.screenshot(path=f'{SC}/h14_quiz_wrong_dark.png')
        assert '틀렸어요' in await (await d.query_selector('#v-quiz .verdict')).inner_text() or '정답은' in await d.inner_text('#v-quiz .verdict')
        await d.click('#grade'); await d.wait_for_timeout(200)
        assert '틀렸어요 · 내일 다시 나와요' in await d.inner_text('#ps-quiz')
        await tidy(d, '어두운 화면')
        await d.screenshot(path=f'{SC}/h15_fin_dark.png', full_page=True)
        await d.context.close()

        bad = [e for e in errs if 'favicon' not in e]
        assert not bad, bad
        print('HOME E2E OK · 콘솔 오류', bad)


asyncio.run(main())
