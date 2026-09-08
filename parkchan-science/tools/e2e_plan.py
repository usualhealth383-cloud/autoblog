#!/usr/bin/env python3
"""일정 E2E — 시간표(학원·학교) · D-day · 시험 일정에 범위 걸기 · 그 범위 문제 풀기.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_plan.py --shots DIR
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/pcs-e2e-plan'
os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(800)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        tabs = await pg.locator('.tab').all_inner_texts()
        assert tabs == ['오늘','교재','문제','일정','통계','내 정보'], tabs
        await pg.click('.tab[data-v="plan"]'); await pg.wait_for_timeout(500)
        await pg.screenshot(path=f'{SC}/p1_empty.png', full_page=True)
        # 시간표 추가
        await pg.click('#ttAdd'); await pg.wait_for_timeout(400)
        await pg.fill('#ttT','박찬 과학 월목반'); await pg.fill('#ttP','2층 A강의실')
        await pg.select_option('#ttG','academy')
        await pg.click('[data-dp="1"]'); await pg.click('[data-dp="4"]')
        await pg.fill('#ttF','19:00'); await pg.fill('#ttE','22:00')
        await pg.click('#ttSave'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('S.sched.fixed.length') == 1
        assert await pg.evaluate('JSON.stringify(S.sched.fixed[0].days)') == '[1,4]'
        # 학교 수업도
        await pg.click('#ttAdd'); await pg.wait_for_timeout(300)
        await pg.fill('#ttT','○○고 2학년'); await pg.select_option('#ttG','school')
        for d in [1,2,3,4,5]: await pg.click(f'[data-dp="{d}"]')
        await pg.fill('#ttF','08:20'); await pg.fill('#ttE','16:40'); await pg.click('#ttSave'); await pg.wait_for_timeout(400)
        # D-day
        await pg.click('#ddAdd'); await pg.wait_for_timeout(400)
        await pg.click('[data-ddp="중간고사"]'); await pg.fill('#ddD','2026-10-14'); await pg.click('#ddSave'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('S.sched.ddays[0].title') == '중간고사'
        assert 'D-' in await pg.locator('.dday .v').inner_text()
        # 시험 일정 + 범위
        await pg.click('#evAdd'); await pg.wait_for_timeout(400)
        await pg.fill('#evT','2학기 중간고사 · 통합과학'); await pg.fill('#evD','2026-10-14')
        await pg.select_option('#evK','exam'); await pg.select_option('#evS','l:1304')
        await pg.fill('#evM','II~III단원, 서술형 2문항'); await pg.click('#evSave'); await pg.wait_for_timeout(600)
        assert await pg.evaluate('S.sched.events[0].scope.lesson') == '1304'
        await pg.screenshot(path=f'{SC}/p2_filled.png', full_page=True)
        # 범위에서 문제 풀기
        await pg.click('[data-ev]'); await pg.wait_for_timeout(500)
        await pg.screenshot(path=f'{SC}/p3_evsheet.png')
        await pg.click('[data-scopego]'); await pg.wait_for_timeout(800)
        assert await pg.evaluate('view') == 'bank'
        assert await pg.evaluate('bs && bs.items.length') == 20
        assert await pg.evaluate('bs.items.every(q=>q.lessonId==="1304")'), '시험 범위 밖 문항이 섞였다'
        await pg.screenshot(path=f'{SC}/p4_drill.png')
        assert not errs, errs
        print('PLAN OK', errs); await b.close()
asyncio.run(main())
