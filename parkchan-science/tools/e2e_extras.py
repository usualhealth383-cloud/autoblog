#!/usr/bin/env python3
"""개념 상세 '생각해 보기'(왜?) · 예제 → 따라 풀기 E2E (2026-10-06, data/concept_extras.json)
· 140개념 모두 생각해 보기가 실렸다 · 본문을 펼친 안쪽에만, 답은 접혀 있다(빈칸 정답이 섞여 있어서) · 예제 개념 20개는 단계·답·따라 풀기
· 답 보기를 누르면 열린다 · 밝은·어두운 화면 가로 넘침 없음
전제: docs/parkchan 이 :8765.   사용: python3 tools/e2e_extras.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_extras'; os.makedirs(SC, exist_ok=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        for scheme in ('light', 'dark'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=scheme, service_workers='block'); await ctx.add_init_script(NO_INTRO)
            s = await ctx.new_page(); await auto_yes(s); s.on('pageerror', lambda e: errs.append(str(e)))
            await s.goto(APP); await s.wait_for_timeout(700); await s.click('#goGuest'); await s.wait_for_timeout(400)
            n = await s.evaluate("[CONCEPTS.filter(c => c.x && c.x.why && c.x.why.q && c.x.why.a).length, CONCEPTS.filter(c => c.x && c.x.example && c.x.follow).length, CONCEPTS.some(c => c.x && c.x.why && 'src' in c.x.why)]")
            assert n[0] == 140 and n[1] >= 20 and n[2] is False, n
            for cid, ex in (('1305-03', False), ('2205-04', True)):
                await s.evaluate(f"detailIdx = CONCEPTS.findIndex(c => c.id === '{cid}'); show('detail')"); await s.wait_for_timeout(400)
                assert await s.locator('#v-detail .dthink').count() == 1 and not await s.locator('#v-detail .dthink').is_visible(), '생각해 보기가 본문 펼치기 바깥에 보임'
                await s.click('#dMoreBtn'); await s.wait_for_timeout(250)
                th = s.locator('#v-detail .dthink'); assert await th.is_visible()
                assert not await th.locator('details').evaluate('d => d.open'), '답이 처음부터 열려 있음'
                await th.locator('summary').click(); await s.wait_for_timeout(150)
                assert await th.locator('details').evaluate('d => d.open') and len(await th.locator('details p').inner_text()) >= 15
                assert (await s.locator('#v-detail .dex').count() == 1) == ex
                if ex:
                    assert await s.locator('#v-detail .exsteps li').count() >= 2 and await s.locator('#v-detail .follow details').count() == 1
                    await s.locator('#v-detail .follow summary').click(); await s.wait_for_timeout(150)
                over = await s.evaluate('document.documentElement.scrollWidth > innerWidth + 1'); assert not over, '가로 넘침'
                await th.scroll_into_view_if_needed(); await s.screenshot(path=f'{SC}/{scheme}_{cid}.png')
                await s.click('#dMoreBtn'); await s.wait_for_timeout(150)   # 다음 시험을 위해 접어 둔다(펼침은 기억된다)
            await ctx.close()
        assert not errs, errs
        print('EXTRAS E2E OK · 콘솔 오류 []'); await b.close()

asyncio.run(main())
