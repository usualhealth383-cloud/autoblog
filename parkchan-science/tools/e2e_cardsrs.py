#!/usr/bin/env python3
"""개념 카드 간격 복습 E2E(2026-10-07 콘텐츠 감사 보완안 7 — 앞면 회상).

날짜는 Playwright 고정 시계로 옮긴다(앱의 todayISO()·addDays() 가 따라온다).
· '공부했음'을 누르면 카드 한 장(S.cs — 오답 기록과 같은 꼴 + ci) · 첫 복습은 내일 · 오늘은 안 나옴
· 다음 날 홈 '하루 경로'의 오늘의 복습에 '개념 카드 1' · 앞면: 제목 · ①②③ 실마리 · 생각해 보기 질문(포인트·답은 아직 안 보임)
  → '떠올렸어요 · 확인하기' → 뒷면(포인트 + 생각해 보기 답) → '기억났어요'(다음 상자, 3일 뒤) / '흐려요'(상자 1, 내일 · k+1)
· 같은 규칙: 1 → 3 → 7 → 14일, 7일 넘게 띄워 두 번 잇달아 기억하면 쉰다(cleared) · 범위에 든 시험이 다가오면 간격이 줄어듦
· 하루 개념 카드 CS_DAY(2)장 · 문제와 합쳐 SRS_CAP(10) 안 · 문제와 섞여 나오고 같은 소단원이 잇달아 나오지 않음
· 생각해 보기 데이터를 받기 전(MORE.ok 전)에는 '포인트를 가린 질문'
· 진도 스냅숏·합치기(더 새 쪽이 이김, 한쪽에만 있는 카드는 남김, 공부한 개념인데 카드가 없으면 넣음) · 서버(로컬 DB) 저장 · 내 기록 내려받기
· 옛 진도(이 기능 전 S.done)도 카드로 · 가로 넘침·말줄임 없음 · 밝은/어두운 스크린샷

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_cardsrs.py [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_cardsrs'; os.makedirs(SC, exist_ok=True)
KST = ZoneInfo('Asia/Seoul')
D0 = dt.date(2026, 10, 5)


def at(day, hh=12):
    return dt.datetime(day.year, day.month, day.day, hh, 0, tzinfo=KST)


def iso(day):
    return day.isoformat()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []

        async def page(color='light', init=None, when=D0):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color, accept_downloads=True)
            await ctx.add_init_script(NO_INTRO)
            if init: await ctx.add_init_script(init)
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
            await pg.evaluate("document.querySelectorAll('.toast').forEach(t => t.remove()); dayRoll(); qState = null; if (bs && bs.kind === 'review') bs = null; revHold = null; show('today')"); await pg.wait_for_timeout(250)

        async def tidy(pg, where):
            r = await pg.evaluate("""(() => ({ sw:document.scrollingElement.scrollWidth, vw:innerWidth,
              ell:[...document.querySelectorAll('main *')].filter(e => getComputedStyle(e).textOverflow === 'ellipsis' && e.offsetParent).map(e => e.className),
              small:[...document.querySelectorAll('#v-bank button')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => e.id || e.className) }))()""")
            assert r['sw'] <= r['vw'] and not r['ell'] and not r['small'], (where, r)

        card = lambda pg: pg.evaluate("(S.cs || []).find(w => w.ci === window.__cid) || null")

        # ───────── 1) 학생 — 공부했음 → 카드 한 장(내일부터) ─────────
        s = await page()
        await s.click('#goLogin'); await s.fill('#lgEmail', 'student@demo.kr'); await s.fill('#lgPw', '1234'); await s.click('#lgGo'); await s.wait_for_timeout(900)
        await s.evaluate('loadMore()'); await s.wait_for_function('MORE.ok', timeout=15000)
        # 옛 진도(이 기능 전에 공부한 개념)도 카드로 — 시연 계정에 이미 있던 공부 기록
        assert await s.evaluate("S.done.every(id => S.cs.some(w => w.ci === id))"), '공부한 개념인데 카드가 없음'
        await s.evaluate("S.done = []; S.cs = []; S.wrong = []; S.bh = {}; S.rv = null; save(S)")   # 시험을 단순하게 — 처음부터
        cid = await s.evaluate("todayConcept().id"); await s.evaluate(f"window.__cid = '{cid}'")
        await s.evaluate("detailIdx = dayIndex(); show('detail')"); await s.wait_for_timeout(300)
        await s.click('#markDone'); await s.wait_for_timeout(250)
        w = await card(s)
        assert w and w['x'] == 1 and w['k'] == 0 and w['iso'] == iso(D0) and w['d'] == iso(D0 + dt.timedelta(1)), w
        assert set(w) <= {'ci', 'iso', 'a', 'd', 'x', 'k', 'g', 'cleared'}, f'카드 기록 칸이 오답 기록 꼴을 벗어남: {w}'
        await s.evaluate("show('today')"); await s.wait_for_timeout(200)
        assert await s.locator('#ps-review.none').count() == 1, '오늘 공부한 개념이 오늘 바로 복습에 나옴'
        snap = await s.evaluate('snapshot()'); assert any(x['ci'] == cid for x in snap['cs']), '진도 스냅숏에 개념 카드가 없음'

        # ───────── 2) 다음 날 — 하루 경로 '오늘의 복습'에 개념 카드 ─────────
        await goto_day(s, D0 + dt.timedelta(1))
        rv = await s.inner_text('#ps-review')
        assert '오늘의 복습 1' in rv and '개념 카드 1' in rv, rv
        await s.screenshot(path=f'{SC}/c01_home_card_due_light.png')
        await s.click('#revStart'); await s.wait_for_timeout(300)
        assert await s.evaluate("bs.kind") == 'review' and await s.evaluate("bs.items[0].type") == 'card'
        c = await s.evaluate(f"(() => {{ const c = CONCEPTS.find(x => x.id === '{cid}'); return {{ title:c.title, point:plain(c.point), why:c.x && c.x.why ? plain(c.x.why.q) : '', a:c.x && c.x.why ? plain(c.x.why.a) : '' }}; }})()")
        front = await s.inner_text('#csCard')
        assert c['title'] in front and c['why'] and c['why'] in front, ('앞면에 제목·생각해 보기 질문이 없음', front)
        assert c['point'][:20] not in front and c['a'][:20] not in front, '확인하기 전에 포인트·답이 보임'
        assert await s.locator('#csFlip').count() == 1 and await s.locator('[data-csr]').count() == 0
        assert '①' in front, '앞면에 단계 실마리(①②③)가 없음'
        await tidy(s, '앞면'); await s.screenshot(path=f'{SC}/c02_front_light.png')
        await s.click('#csFlip'); await s.wait_for_timeout(200)
        back = await s.inner_text('#csCard'); assert c['point'][:20] in back and c['a'][:20] in back, back
        assert await s.locator('[data-csr]').count() == 2 and await s.evaluate("document.activeElement.dataset.csr") == 'o', '확인한 뒤 초점이 기억났어요로 가지 않음'
        await tidy(s, '뒷면'); await s.screenshot(path=f'{SC}/c03_back_light.png')
        await s.click('[data-csr="o"]'); await s.wait_for_timeout(250)
        w = await card(s); d1 = D0 + dt.timedelta(1)
        assert w['x'] == 2 and w['a'] == iso(d1) and w['d'] == iso(d1 + dt.timedelta(3)) and w['k'] == 0, w
        fb = await s.inner_text('#v-bank .verdict.fb'); assert '기억났어요' in fb and '간격을 넓혀요' in fb and '3일 뒤' in fb, fb
        assert await s.evaluate("rvToday().c") == 1 and await s.evaluate("S.stats.a") == 0, '개념 카드가 문제 풀이 수로 셈'
        await s.screenshot(path=f'{SC}/c04_rated_light.png')
        await s.click('#bankNext'); await s.wait_for_timeout(200)
        assert '오늘의 복습을 마쳤어요' in await s.inner_text('#v-bank')
        await s.click('#bankQuit2'); await s.wait_for_timeout(200)
        assert await s.locator('#ps-review.done').count() == 1, '카드를 끝냈는데 복습 단계가 끝나지 않음'
        assert '3일 뒤' in await s.inner_text('#ps-review'), await s.inner_text('#ps-review')

        # ───────── 3) 흐려요 → 상자 1(내일) · k+1 ─────────
        d4 = d1 + dt.timedelta(3)
        await goto_day(s, d4)
        await s.click('#revStart'); await s.wait_for_timeout(250)
        await s.click('#csFlip'); await s.wait_for_timeout(120); await s.click('[data-csr="x"]'); await s.wait_for_timeout(200)
        w = await card(s); assert w['x'] == 1 and w['k'] == 1 and w['d'] == iso(d4 + dt.timedelta(1)), w
        fb = await s.inner_text('#v-bank .verdict.fb'); assert '흐려도 괜찮아요' in fb and '내일' in fb, fb
        await s.click('#bankNext'); await s.wait_for_timeout(150); await s.click('#bankQuit2'); await s.wait_for_timeout(150)

        # ───────── 4) 같은 규칙: 1 → 3 → 7 → 14, 7일 넘게 두 번 잇달아 기억하면 쉰다 ─────────
        d = d4 + dt.timedelta(1); chain = []
        for gap in (3, 7, 14, None):
            await goto_day(s, d)
            r = await s.evaluate(f"(() => {{ const r = csMark('{cid}', true); return r && {{ st:r.st, d:r.d || '' }}; }})()")
            chain.append(r['st'])
            if gap: assert r['d'] == iso(d + dt.timedelta(gap)), (gap, r); d = d + dt.timedelta(gap)
        assert chain == ['up', 'up', 'up', 'clear'], chain
        assert (await card(s))['cleared'] is True
        await s.evaluate("save(S)"); await goto_day(s, d + dt.timedelta(40))
        assert await s.evaluate("csToday().length") == 0, '쉬는 카드가 다시 나옴'
        # 범위에 든 시험이 다가오면 간격이 줄어든다(문제와 같은 srsGap)
        await s.evaluate(f"(() => {{ const w = S.cs.find(x => x.ci === '{cid}'); delete w.cleared; w.x = 3; w.d = todayISO(); w.a = addDays(todayISO(), -7); S.sched.ddays.push({{ id:'dd-t', title:'중간고사', date:addDays(todayISO(), 6) }}); }})()")
        r = await s.evaluate(f"csMark('{cid}', true)"); assert r['d'] == await s.evaluate("addDays(todayISO(), 1)"), ('시험 6일 전인데 간격이 줄지 않음', r)
        await s.evaluate("S.sched.ddays = S.sched.ddays.filter(x => x.id !== 'dd-t'); save(S)")

        # ───────── 5) 하루 CS_DAY 장 · 문제와 합쳐 SRS_CAP · 섞어 내기 ─────────
        dX = d + dt.timedelta(60)
        await goto_day(s, dX)
        await s.evaluate("""(() => { const t = todayISO(), y = addDays(t, -1), seen = new Set(), ids = [];
          for (const c of CONCEPTS){ if (!seen.has(c.lessonId) && ids.length < 5){ seen.add(c.lessonId); ids.push(c.id); } }
          S.done = ids.slice(); S.cs = ids.map(id => ({ ci:id, iso:y, a:y, d:y, x:1, k:0 }));
          const qs = BANK.filter(q => !isUM(q) && q.type === 'ox' && !ids.some(id => id.startsWith(q.lessonId))).slice(0, 12);
          S.wrong = qs.map(q => ({ b:q.id, p:'O', iso:y, a:y, d:y, x:1, k:1 })); S.bh = {}; S.rv = null; save(S); show('today'); })()""")
        await s.wait_for_timeout(200)
        assert await s.evaluate("CS_DAY") == 2 and await s.evaluate("csToday().length") == 2, '하루 개념 카드가 2장이 아님'
        assert await s.evaluate("dueToday().length") == 8, '개념 카드 몫(2)을 빼고 문제 8개가 아님'
        plan = await s.evaluate("reviewPlan(true).items.map(e => ({ k: e.cs ? 'c' : e.w ? 'w' : 'x', l: e.lesson }))")
        assert sum(1 for e in plan if e['k'] == 'c') == 2 and sum(1 for e in plan if e['k'] == 'w') == 3, plan
        assert all(plan[i]['l'] != plan[i + 1]['l'] for i in range(len(plan) - 1)), ('같은 소단원이 잇달아 나옴', plan)
        assert '개념 카드 2' in await s.inner_text('#ps-review')
        await s.click('#revStart'); await s.wait_for_timeout(250)
        kinds = await s.evaluate("bs.items.map(q => q.type === 'card' ? 'c' : 'q')"); assert kinds.count('c') == 2 and kinds.count('q') >= 3, kinds
        while await s.evaluate("bs.i < bs.items.length"):
            t = await s.evaluate("bs.items[bs.i].type")
            if t == 'card':
                await s.click('#csFlip'); await s.wait_for_timeout(80); await s.click('[data-csr="o"]')
            else:
                q = await s.evaluate("(() => { const q = bs.items[bs.i]; return { type:q.type, answer:q.answer }; })()")
                if q['type'] == 'ox': await s.click(f'[data-ox="{q["answer"]}"]')
                elif q['type'] in ('mc', 'multi'): await s.click(f'[data-bp="{q["answer"]}"]')
                elif q['type'] == 'blank': await s.fill('#blankIn', str(q['answer'])); await s.click('#blankGo')
                else: await s.click('#essayShow'); await s.wait_for_timeout(80); await s.click('[data-ess="맞음"]')
            await s.wait_for_timeout(120); await s.click('#bankNext'); await s.wait_for_timeout(120)
        assert await s.evaluate("rvToday().c") == 2 and await s.evaluate("csToday().length") == 0, '하루 2장을 넘김'
        assert await s.evaluate("(S.cs || []).filter(w => isDueW(w)).length") == 3, '남은 카드는 내일로'
        await s.click('#bankQuit2'); await s.wait_for_timeout(150)
        # 문제를 거의 다 풀었으면 카드도 상한 안에서 — 문제 9 + 카드 0 → 카드 1장만
        await s.evaluate("S.rv = { d:todayISO(), n:9, s:1, c:0 }")
        assert await s.evaluate("csToday().length") == 1 and await s.evaluate("dueToday().length") == 0, await s.evaluate("[csToday().length, dueToday().length]")

        # ───────── 6) 생각해 보기를 받기 전 — 포인트를 가린 질문 ─────────
        fq = await s.evaluate(f"(() => {{ const c = CONCEPTS.find(x => x.id === '{cid}'); return csFront({{ ...c, x:null }}); }})()")
        assert '포인트를 한 문장으로 떠올려' in fq['q'] and not fq['a'], fq

        # ───────── 7) 동기화 · 서버(로컬 DB) · 내 기록 내려받기 ─────────
        await s.evaluate("S.rv = null; save(S)")
        a_id = await s.evaluate("S.cs[0].ci"); b_id = await s.evaluate("S.cs[1].ci")
        await s.evaluate(f"""mergeProgress({{ cs:[{{ ci:'{a_id}', iso:'2026-01-01', a:'2026-01-01', d:'2027-01-01', x:4, k:2 }}, {{ ci:'9999-99', iso:'2026-01-01', a:'2026-01-01', d:'2027-01-01', x:1, k:0 }}],
            done:['{cid}'], at:new Date(Date.now() + 5000).toISOString() }})""")
        m = await s.evaluate("S.cs.map(w => [w.ci, w.x])")
        assert [a_id, 4] in m, ('더 새 스냅숏의 카드가 이기지 않음', m)
        assert any(x[0] == b_id for x in m), ('한쪽에만 있는 카드가 사라짐', m)
        assert any(x[0] == cid for x in m), '합친 공부 기록에 카드가 없음'
        await s.evaluate("flushProgress()"); await s.wait_for_timeout(400)
        srv = await s.evaluate("(async () => { const p = await DBX.loadProgress(progressKey()); return (p && p.cs || []).map(w => w.ci); })()")
        assert a_id in srv and cid in srv, ('서버(로컬 DB) 진도에 개념 카드가 없음', srv)
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(400)
        async with s.expect_download() as dl: await s.click('#myExport')
        f = await dl.value; j = json.loads(open(await f.path(), encoding='utf-8').read())
        assert any(w['ci'] == a_id for w in j['학습']['개념_카드_복습']), list(j['학습'])
        # 깨진 기록은 걸러진다
        await s.evaluate("localStorage.setItem('pcs.v2', JSON.stringify({ ...JSON.parse(localStorage.getItem('pcs.v2')), cs:[null, 3, { x:1 }, { ci:'1101-01', d:'2026-01-01', x:1, k:0, iso:'2026-01-01' }] }))")
        assert await s.evaluate("fixS(JSON.parse(localStorage.getItem('pcs.v2'))).cs.length") == 1
        await s.context.close()

        # ───────── 8) 어두운 화면 · 손님(로그인 없이)도 같은 흐름 ─────────
        g = await page('dark')
        await g.click('#goGuest'); await g.wait_for_timeout(300)
        await g.evaluate('loadMore()'); await g.wait_for_function('MORE.ok', timeout=15000)
        await g.evaluate("detailIdx = dayIndex(); show('detail')"); await g.wait_for_timeout(200); await g.click('#markDone'); await g.wait_for_timeout(200)
        await goto_day(g, D0 + dt.timedelta(1))
        await g.screenshot(path=f'{SC}/c11_home_card_due_dark.png')
        await g.click('#revStart'); await g.wait_for_timeout(250); await tidy(g, '어두운 앞면'); await g.screenshot(path=f'{SC}/c12_front_dark.png')
        await g.click('#csFlip'); await g.wait_for_timeout(150); await g.screenshot(path=f'{SC}/c13_back_dark.png')
        await g.click('[data-csr="x"]'); await g.wait_for_timeout(200); await tidy(g, '어두운 채점'); await g.screenshot(path=f'{SC}/c14_rated_dark.png')
        await g.context.close()

        bad = [e for e in errs if 'favicon' not in e]
        assert not bad, bad
        print('CARD SRS E2E OK · 콘솔 오류', bad)


asyncio.run(main())
