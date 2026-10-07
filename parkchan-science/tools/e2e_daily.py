#!/usr/bin/env python3
"""하루 흐름 보완 E2E — 원장님 결정 2026-10-07(7일 사용 점검 뒤).

· 오늘의 문제 = 그 개념에 묶인 문제 은행 고르는 문제(선다·합답) 중 안 푼 것 — 하루 동안 같은 문제, 다시 열면 채점된 그대로,
  개념이 적은 소단원(I-01)에서도 날마다 다른 문제, 푼 문제는 다음에 안 나옴, 은행 기록(S.bh)·간격 복습({b:id})에 같이 남음
· 어제 못 본 개념 — 어제 개념을 읽지도 끝내지도 않았으면 경로 아래 조용한 한 줄(누르면 그 개념), 첫날·읽었으면 없음
· 출석 체크 — 수강생(학원 코드)에게만, 수강 기간이 끝난 코드면 안 뜸
· 가로 넘침·말줄임 없음 · 밝은/어두운 스크린샷

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_daily.py
"""
import asyncio, sys, os, datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = '/tmp/e2e_daily'; os.makedirs(SC, exist_ok=True)
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 6)
iso = lambda d: d.isoformat()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []

        async def page(color='light'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color)
            await ctx.add_init_script(NO_INTRO)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await pg.clock.set_fixed_time(dt.datetime(D0.year, D0.month, D0.day, 12, tzinfo=KST))
            await auto_yes(pg)
            await pg.goto(APP); await pg.wait_for_timeout(700)
            return pg

        # ───────── 1) 오늘의 문제 = 문제 은행 ─────────
        s = await page()
        await s.evaluate(f"(() => {{ S.start = '{iso(D0)}'; S.tp = null; S.bh = {{}}; S.wrong = []; save(S); }})()")
        await s.evaluate("loadMore()"); await s.wait_for_function('MORE.ok', timeout=15000)
        q = await s.evaluate("(() => { const c = todayConcept(), q = todayQ(c); return { id:q.id, l:q.lessonId, k:+q.concept, t:q.type, step:q.step, cl:c.lessonId, cn:+c.no }; })()")
        assert q['id'] and q['l'] == q['cl'] and q['k'] == q['cn'] and q['t'] in ('mc', 'multi') and q['step'] != 'auto', q
        # I-01(개념 5개)에서 닷새 동안 — 날마다 다른 문제(예전엔 강의용 확인 문제가 이틀마다 되풀이)
        ids = await s.evaluate("""(() => { const out = []; for (let d = 0; d < 5; d++){ const c = CONCEPTS[d]; S.tp = { d:todayISO(), c:c.id }; out.push(todayQ(c).id); } S.tp = null; return out; })()""")
        assert len(set(ids)) == 5, ('I-01 오늘의 문제가 되풀이됨', ids)
        # 같은 날 다시 불러도 같은 문제
        assert await s.evaluate("todayQ(todayConcept()).id") == await s.evaluate("todayQ(todayConcept()).id")
        # 풀기 — 홈 경로에서 들어가 고르기
        await s.evaluate("show('today')"); await s.wait_for_timeout(200)
        await s.evaluate("tpToday().read = 1; markRead(todayConcept().id); tpToday().b = [1,1,1]; save(S); show('today')"); await s.wait_for_timeout(200)
        await s.click('#goQuiz'); await s.wait_for_timeout(300)
        got = await s.evaluate("qState.q.id"); assert got == q['id'], (got, q)
        assert await s.locator('#v-quiz .stem').count() == 1 and await s.locator('#v-quiz .opt').count() == 5
        ans = await s.evaluate('qState.q.answer'); wrong = 1 if ans != 1 else 2
        await s.click(f'#v-quiz .opt[data-p="{wrong}"]'); await s.wait_for_timeout(250)
        st = await s.evaluate(f"(() => ({{ tq:S.tp.q, qid:S.tp.qid, bh:S.bh['{q['id']}'], w:!!findW({{ b:'{q['id']}' }}) }}))()")
        assert st == {'tq': 'x', 'qid': q['id'], 'bh': 'x', 'w': True}, st
        assert await s.locator('#v-quiz .flag[data-report="bank:' + q['id'] + '"]').count() == 1, '틀린 곳 알리기가 은행 문항 id 로 안 감'
        assert await s.locator('#v-quiz .expl, #v-quiz .verdict').count() >= 1
        await s.screenshot(path=f'{SC}/d01_today_q_graded.png', full_page=True)
        # 다시 열면 채점된 그대로(같은 문제)
        await s.reload(); await s.wait_for_timeout(800); await s.evaluate("loadMore()"); await s.wait_for_function('MORE.ok', timeout=15000)
        await s.evaluate("show('today')"); await s.wait_for_timeout(200)
        await s.click('#goQuiz'); await s.wait_for_timeout(300)
        assert await s.evaluate("[qState.q.id, qState.pick]") == [q['id'], wrong]
        assert await s.locator('#v-quiz .opt.bad').count() == 1
        # 다음에 같은 개념이 돌아와도 푼 문제는 안 나옴
        nxt = await s.evaluate("(() => { const keep = S.tp; S.tp = null; const id = todayQ(todayConcept()).id; S.tp = keep; return id; })()")
        assert nxt != q['id'], '푼 문제가 다시 오늘의 문제로'

        # ───────── 2) 어제 못 본 개념 ─────────
        await s.evaluate(f"(() => {{ S.start = '{iso(D0 - dt.timedelta(1))}'; S.done = []; S.read = []; S.tp = null; save(S); show('today'); }})()"); await s.wait_for_timeout(250)
        y = await s.evaluate("CONCEPTS[0].title")
        line = s.locator('#v-today .pmiss'); assert await line.count() == 1 and y in await line.inner_text(), '어제 못 본 개념 한 줄이 없음'
        r = await s.evaluate("""(() => { const e = document.querySelector('#v-today .pmiss span'), cs = getComputedStyle(e); return { fs:parseFloat(cs.fontSize), wb:cs.wordBreak, sw:document.scrollingElement.scrollWidth, vw:innerWidth, ell:cs.textOverflow }; })()""")
        assert r['sw'] <= r['vw'] and r['ell'] != 'ellipsis' and r['wb'] == 'keep-all', r
        assert await s.locator('#v-today .pnow').count() == 1, '한 줄이 큰 카드가 됨(화면당 히어로 하나)'
        await s.screenshot(path=f'{SC}/d02_miss_line.png', full_page=True)
        await s.click('#pMiss'); await s.wait_for_timeout(300)
        assert await s.evaluate("[document.querySelector('.view.on, section.on')?.id || location.hash, detailIdx]") is not None
        assert await s.evaluate("detailIdx") == 0 and y in await s.locator('#v-detail').inner_text(), '누르면 어제 개념이 안 열림'
        await s.evaluate("markRead(CONCEPTS[0].id); save(S); show('today')"); await s.wait_for_timeout(200)
        assert await s.locator('#v-today .pmiss').count() == 0, '어제 개념을 읽었는데도 한 줄이 남음'
        await s.evaluate(f"(() => {{ S.start = '{iso(D0)}'; S.read = []; save(S); show('today'); }})()"); await s.wait_for_timeout(200)
        assert await s.locator('#v-today .pmiss').count() == 0, '첫날에 어제 개념 한 줄'

        # ───────── 3) 출석 체크는 수강생에게만 ─────────
        await s.evaluate("(() => { S.auth = null; save(S); renderToday(); })()"); await s.wait_for_timeout(300)
        assert await s.locator('#attOpen').count() == 0, '수강생 아닌 사람에게 출석 체크'
        await s.evaluate(f"(() => {{ S.auth = {{ code:'X0', name:'시험', cls:'월목반', until:'{iso(D0 - dt.timedelta(1))}' }}; save(S); renderToday(); }})()"); await s.wait_for_timeout(400)
        assert await s.locator('#attOpen').count() == 0, '수강 기간이 끝난 코드에 출석 체크'
        await s.evaluate("(() => { S.auth = null; save(S); })()")

        # 어두운 화면
        dk = await page('dark')
        await dk.evaluate(f"(() => {{ S.start = '{iso(D0 - dt.timedelta(1))}'; S.done = []; S.read = []; save(S); show('today'); }})()"); await dk.wait_for_timeout(300)
        await dk.screenshot(path=f'{SC}/d03_miss_line_dark.png', full_page=True)

        await b.close()
        assert not errs, errs
        print('DAILY E2E OK · 콘솔 오류', errs)

asyncio.run(main())
