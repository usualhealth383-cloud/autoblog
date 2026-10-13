#!/usr/bin/env python3
"""학평 범위 채우기 · 보호자 출석 알림 끄기 · 워터마크 옅게 · 한 마디 접기(2026-10-13 원장님 결정 반영)
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_hakpyeong.py
"""
import asyncio, sys, os, urllib.parse
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg); await pg.goto('http://127.0.0.1:8765/index.html?server='); await pg.wait_for_timeout(700)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        await pg.wait_for_function('MORE.ok', timeout=20000)
        # 한 마디: 글귀·사람만 보이고 원문·출처·과학으로 잇기는 접힘
        assert await pg.locator('.qsay details.qmore').count() == 1 and not await pg.locator('.qsay details.qmore').evaluate('d => d.open')
        # 워터마크: 옅게(0.045)·간격 360
        bg = urllib.parse.unquote(await pg.evaluate("document.getElementById('wm').style.backgroundImage"))
        assert 'width="360"' in bg and ('0.045' in bg or '0.05' in bg) and 'font-weight="400"' in bg, bg[:200]
        # 학평 범위: 일정 추가 → 고1 9월 학평 → 이름·범위 채움 → 저장 → 시험까지 계획이 그 범위로
        R = await pg.evaluate("HAKP.map(h => [h.k, h.ls().length])")
        n1 = await pg.evaluate("LESSONS.filter(l => l.book === '1').length")
        assert dict(R)['h9'] == n1 + 1 and dict(R)['h2'] == await pg.evaluate('LESSONS.length') and dict(R)['h6'] < n1, R
        await pg.evaluate("show('plan')"); await pg.wait_for_timeout(400); await pg.click('#evAdd'); await pg.wait_for_timeout(400)
        await pg.click('[data-hp="h9"]'); await pg.wait_for_timeout(200)
        assert '9월 학력평가' in await pg.input_value('#evT') and await pg.input_value('#evS') == 'p:h9'
        await pg.fill('#evD', await pg.evaluate("addDays(todayISO(), 12)")); await pg.click('#evSave'); await pg.wait_for_timeout(500)
        e = await pg.evaluate("(() => { const e = S.sched.events.find(x => x.scope && x.scope.preset === 'h9'); return e && { n:e.scope.lessons.length, name:scopeName(e.scope), plan:!!examPlan(e), ls:examPlan(e).ls.length }; })()")
        assert e and e['n'] == n1 + 1 and '통합과학2 Ⅰ-1' in e['name'] and e['plan'] and e['ls'] == n1 + 1, e
        await pg.evaluate("drillScope(S.sched.events.find(x => x.scope && x.scope.preset === 'h9').scope)"); await pg.wait_for_timeout(500)
        ok = await pg.evaluate("bs.items.length === 20 && bs.items.every(q => q.lessonId.startsWith('1') || q.lessonId === '2101')"); assert ok, '학평 범위 밖 문항'
        # 보호자: 출석 알림 끄기·켜기
        await pg.evaluate("bs = null; show('me')"); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(700)
        await pg.click('#goLogin'); await pg.click('[data-demo^="parent"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
        assert await pg.get_attribute('#atPush', 'aria-pressed') == 'true'
        await pg.click('#atPush'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('ACC.attendOff') is True and await pg.get_attribute('#atPush', 'aria-pressed') == 'false' and '끔' in await pg.inner_text('#atPush')
        await pg.click('#atPush'); await pg.wait_for_timeout(500); assert await pg.evaluate('ACC.attendOff') is False
        assert not errs, errs
        print('HAKPYEONG OK'); await b.close()
asyncio.run(main())
