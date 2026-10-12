#!/usr/bin/env python3
"""이용권 끝나기 전 예고(벤치마크 #19) — 7일·1일 전·오늘·끝난 뒤 한 줄, 닫으면 그 단계엔 다시 안 뜸, 수강생·원장에겐 안 뜸.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_passnote.py
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-passnote'; os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg)
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(800)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        # 학원 수강생 — 이용권이 있어도 안 뜸
        await pg.evaluate("ACC.passUntil = addDays(todayISO(), 3); renderToday()"); await pg.wait_for_timeout(300)
        assert await pg.locator('.passnote').count() == 0, '수강생에게 이용권 예고가 떴다'
        # 수강생 아닌 이용권 이용자로
        async def at(days):
            await pg.evaluate(f"S.auth = null; ACC.passUntil = addDays(todayISO(), {days}); renderToday()"); await pg.wait_for_timeout(300)
            n = pg.locator('.passnote'); return (await n.inner_text()) if await n.count() else ''
        assert await at(20) == '', '20일 남았는데 떴다'
        t = await at(7); assert '7일' in t and '자동 결제는 없어요' in t, t
        await pg.screenshot(path=f'{SC}/n1_d7.png')
        await pg.click('#passNoteX'); await pg.wait_for_timeout(200)
        await pg.evaluate("renderToday()"); await pg.wait_for_timeout(300)
        assert await pg.locator('.passnote').count() == 0, '닫았는데 같은 단계(7일 전)에 다시 떴다'
        t = await at(1); assert '1일' in t, '1일 전 단계는 닫은 것과 따로 떠야 한다: ' + t
        t = await at(0); assert '오늘' in t, t
        t = await at(-3); assert '끝났어요' in t and '기록은 그대로' in t, t
        await pg.screenshot(path=f'{SC}/n2_end.png')
        await pg.click('#passNoteGo'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('view') == 'plans', await pg.evaluate('view')
        assert await at(-9) == '', '끝나고 7일이 지났는데 떴다'
        assert not errs, errs
        print('PASSNOTE OK'); await b.close()
asyncio.run(main())
