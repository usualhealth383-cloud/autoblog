#!/usr/bin/env python3
"""과제 서술형(★4 마지막) — 원장이 '서술형'을 골라 내고 · '유형 전체'에는 서술형이 안 섞이고 · 학생은 써 본 뒤 모범 답안과 견주어 스스로 채점 → 냄 · 보고서에 '스스로 채점' 안내.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_asg_essay.py
"""
import asyncio, sys, os, datetime as dt
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-asgessay'; os.makedirs(SC, exist_ok=True)
APP = 'http://127.0.0.1:8765/index.html?server='
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700)
        async def login(em, pw):
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1300)
        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(800)
        await login('owner@parkchan.kr', '2580')
        await pg.click('[data-adm="asg"]'); await pg.wait_for_selector('#asgForm'); await pg.wait_for_function('MORE.ok', timeout=20000); await pg.wait_for_timeout(400)
        L = await pg.evaluate("(LESSONS.find(l => BANK.filter(q => q.lessonId === l.id && q.type === 'essay' && !isUM(q)).length >= 2) || {}).id")
        assert L, '서술형이 2개 넘는 소단원이 없다'
        await pg.select_option('#afLesson', L); await pg.wait_for_timeout(150)
        # 유형 전체 → 서술형 안 섞임
        mixed = await pg.evaluate("asgPool({ ...asgF, type:'전체', diff:'전체' }).some(q => q.type === 'essay')"); assert not mixed, '유형 전체에 서술형이 섞였다'
        await pg.click('#asgForm [data-af="type"][data-val="essay"]'); await pg.wait_for_timeout(150)
        await pg.click('#asgForm [data-af="n"][data-val="5"]'); await pg.wait_for_timeout(100)
        await pg.select_option('#afCls', '월목반'); await pg.wait_for_timeout(150)
        summ = await pg.inner_text('#afSum'); assert '(서술형)' in summ and '스스로 채점' in summ, summ
        await pg.screenshot(path=f'{SC}/e1_form.png', full_page=True)
        await pg.click('#afSend'); await pg.wait_for_timeout(1100)
        n = await pg.evaluate("(async () => (await DBX.assignList())[0].n)()"); assert n >= 2, n
        await logout(); await login('student@demo.kr', '1234')
        if await pg.evaluate('view') != 'today': await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(900)
        await pg.locator('.asgcard', has_text='서술형').click(); await pg.wait_for_timeout(700)
        assert await pg.evaluate("bs.kind") == 'asg' and await pg.evaluate("bs.items.every(q => q.type === 'essay')")
        for k in range(n):
            await pg.fill('#essayIn', '전자가 원자핵 둘레를 돌며 에너지 준위를 가진다.')
            await pg.click('#essayShow'); await pg.wait_for_timeout(200)
            if k == 0:
                t = await pg.inner_text('#v-bank'); assert '모범 답안' in t, t[:300]; await pg.screenshot(path=f'{SC}/e2_selfgrade.png')
            await pg.click(f'[data-ess="{"맞음" if k % 2 == 0 else "틀림"}"]'); await pg.wait_for_timeout(250)
            await pg.click('#bankNext'); await pg.wait_for_timeout(300)
        await pg.wait_for_timeout(900)
        res = await pg.inner_text('#v-bank'); assert '학원에 냈어요' in res, res[:300]
        right = (n + 1) // 2; assert f'{right} / {n}' in res, (right, n, res[:200])
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(700)
        await logout(); await login('owner@parkchan.kr', '2580')
        await pg.click('[data-adm="asg"]'); await pg.wait_for_selector('#asgForm'); await pg.wait_for_timeout(500)
        await pg.locator('[data-asgrep]').first.click(); await pg.wait_for_timeout(800)
        sh = await pg.inner_text('.sheet'); assert '스스로 채점한 결과' in sh and '제출' in sh, sh[:400]
        await pg.screenshot(path=f'{SC}/e3_report.png')
        assert not errs, errs
        print('ASG ESSAY OK', n); await b.close()
asyncio.run(main())
