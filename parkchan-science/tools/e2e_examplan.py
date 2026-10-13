#!/usr/bin/env python3
"""시험까지 계획(벤치마크 #12·#13) — 범위를 건 시험 → 남은 날 × 소단원 하루 분량, 마지막 3일 섞어 풀기(약한 곳·꼭 볼 문항 먼저),
홈 14일 안 한 줄, 오늘 분량 풀기 → 끝 표시, 하루 빠져도 오늘부터 다시 짬.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_examplan.py
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-examplan'; os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg); await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(800)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        await pg.wait_for_function('MORE.ok', timeout=20000)
        # 계획 모양 — 10일 남음 · 통합과학 1 전체
        P = await pg.evaluate("(() => { const P = examPlan({ id:'x', kind:'exam', title:'중간', date:addDays(todayISO(), 10), scope:{ book:'1' } }); return { d:P.d, n:P.ls.length, k:P.rows.map(r => r.kind), first:P.rows[0].date === todayISO(), cover:[...new Set(P.rows.filter(r => r.kind === 'learn').flatMap(r => r.lessons))].length }; })()")
        assert P['d'] == 10 and len(P['k']) == 10 and P['k'][-3:] == ['mix'] * 3 and P['first'], P
        assert P['cover'] == P['n'], ('범위 소단원이 모두 계획에 들어가야 한다', P)
        P2 = await pg.evaluate("examPlan({ id:'y', kind:'exam', title:'쪽지', date:addDays(todayISO(), 2), scope:{ lesson:'1101' } }).rows.map(r => r.kind)")
        assert P2 == ['learn', 'weak'], P2
        P3 = await pg.evaluate("examPlan({ id:'z', kind:'exam', title:'지난 시험', date:todayISO(), scope:{ book:'1' } })"); assert P3 is None, '시험 당일·지난 시험은 계획 없음'
        P4 = await pg.evaluate("examPlan({ id:'w', kind:'etc', title:'행사', date:addDays(todayISO(), 5), scope:{ book:'1' } })"); assert P4 is None, '시험이 아니면 계획 없음'
        # 섞어 풀기: 20문제, 약한 소단원 먼저, 같은 소단원 연달아 거의 없음, 서술형 없음
        mx = await pg.evaluate("""(() => { const P = examPlan({ id:'x', kind:'exam', title:'중간', date:addDays(todayISO(), 10), scope:{ book:'1' } }), r = P.rows[9], it = planItems(r, P.ls);
            return { n:it.length, ess:it.some(q => q.type === 'essay'), weak:it.filter(q => r.lessons.includes(q.lessonId)).length, all:it.every(q => P.ls.includes(q.lessonId)) }; })()""")
        assert mx['n'] == 20 and not mx['ess'] and mx['weak'] == 0 and mx['all'], ('기록이 없으면 약한 곳 없이 범위 전체에서', mx)
        # 기록이 생기면: I-02 를 5문제 중 1개만 맞힘 → 약한 곳으로, 섞어 풀기의 절반 넘게가 아니라 앞자리 몫(4문제 이상)
        await pg.evaluate("(() => { S.bh ||= {}; BANK.filter(q => q.lessonId === '1102' && !isUM(q) && q.type !== 'essay').slice(0, 5).forEach((q, i) => S.bh[q.id] = i ? 'x' : 'o'); })()")
        mx2 = await pg.evaluate("""(() => { const P = examPlan({ id:'x', kind:'exam', title:'중간', date:addDays(todayISO(), 10), scope:{ book:'1' } }), r = P.rows[9], it = planItems(r, P.ls);
            return { L:r.lessons, n:it.filter(q => q.lessonId === '1102').length, txt:planRowText(r) }; })()""")
        assert mx2['L'] == ['1102'] and mx2['n'] >= 4 and '약한 곳 I-02 먼저' in mx2['txt'], mx2
        # 일정에 시험 넣기(UI) → 시트에 '시험까지 계획'
        await pg.evaluate("S.sched.events.push({ id:'ex1', date:addDays(todayISO(), 9), title:'2학기 중간고사', kind:'exam', from:'', memo:'', scope:{ book:'1' } }); save(S)")
        await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(700)
        note = await pg.locator('.exchip', has_text='중간고사').inner_text(); assert 'D-9' in note and '시험까지 계획' in note, note
        await pg.click('[data-eplan="ex1"]'); await pg.wait_for_timeout(500)
        sh = await pg.inner_text('.sheet'); assert '시험까지 계획' in sh and '오늘' in sh and '섞어 풀기 20문제' in sh and '약한 곳 I-02' in sh and '2학기 중간고사' in sh, sh
        rows = await pg.locator('.eplan li').count(); assert rows == 10, rows   # 9일 + 시험날
        clip = await pg.evaluate("[...document.querySelectorAll('.eplan li .tx')].filter(e => e.scrollWidth > e.clientWidth + 1).length"); assert clip == 0, '계획 줄 글자 넘침'
        await pg.screenshot(path=f'{SC}/x1_plan.png', full_page=True)
        await pg.click('#planGo'); await pg.wait_for_timeout(700)
        assert await pg.evaluate("view") == 'bank' and await pg.evaluate("bs.kind") == 'plan' and await pg.evaluate("bs.items.length") == 10
        for k in range(10):
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer }; })()")
            if q['t'] == 'ox': await pg.click(f'[data-ox="{q["a"]}"]')
            elif q['t'] in ('mc', 'multi'): await pg.click(f'[data-bp="{q["a"]}"]')
            else: await pg.fill('#blankIn', str(q['a'])); await pg.click('#blankGo')
            await pg.wait_for_timeout(200); await pg.click('#bankNext'); await pg.wait_for_timeout(200)
        assert await pg.evaluate("S.epd && S.epd.ex1") == await pg.evaluate("todayISO()"), '오늘 분량 끝이 남지 않음'
        await pg.click('#bankQuit2'); await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(600)
        assert '오늘 분량 끝났어요' in await pg.locator('.exchip', has_text='중간고사').inner_text()
        # 시험 15일 전이면 홈에 안 뜸
        await pg.evaluate("S.sched.events[S.sched.events.length-1].date = addDays(todayISO(), 15); save(S); renderToday()"); await pg.wait_for_timeout(400)
        assert await pg.locator('.exchip', has_text='중간고사').count() == 0
        assert not errs, errs
        print('EXAMPLAN OK'); await b.close()
asyncio.run(main())
