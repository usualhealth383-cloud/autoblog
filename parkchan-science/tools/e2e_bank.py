#!/usr/bin/env python3
"""문제 은행·자료 탐구·그림 확대 보기 E2E (로컬 어댑터).
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤 실행 — 스크린샷은 --shots DIR 에 저장.
  cd docs/parkchan && python3 -m http.server 8765 &
  python3 tools/e2e_bank.py --shots /tmp/shots
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv else '/tmp/pcs-e2e-bank'
os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); ctx = await b.new_context(viewport={'width':400,'height':820}, device_scale_factor=2); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'ERR_' not in m.text else None)
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(600)
        await pg.click('#goLogin'); await pg.fill('#lgEmail','student@demo.kr'); await pg.fill('#lgPw','1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(700)
        assert [t for t in await pg.locator('.tab').all_inner_texts()]==['오늘','교재','문제','이야기','일정','내 정보']
        await pg.click('.tab[data-v="bank"]'); await pg.wait_for_timeout(400); await pg.screenshot(path=f'{SC}/b1_bank.png', full_page=True)
        t = await pg.locator('#v-bank').inner_text(); assert '1,695' in t and '자료 탐구' in t, t[:200]
        await pg.click('[data-bsel="type"][data-val="ox"]'); await pg.wait_for_timeout(200); await pg.click('#bankStart'); await pg.wait_for_timeout(400)
        assert await pg.evaluate('bs && bs.items.length')==10 and await pg.evaluate('bs.items.every(q=>q.type==="ox")')
        for i in range(10):
            ans = await pg.evaluate('bs.items[bs.i].answer'); pick = ans if i%3 else ('X' if ans=='O' else 'O')
            await pg.click(f'[data-ox="{pick}"]'); await pg.wait_for_timeout(150)
            if i==0: await pg.screenshot(path=f'{SC}/b2_ox_graded.png', full_page=True)
            await pg.click('#bankNext'); await pg.wait_for_timeout(150)
        r = (await pg.locator('.result').inner_text()).replace('\n',' '); assert '6' in r, r; await pg.screenshot(path=f'{SC}/b3_result.png', full_page=True)
        assert await pg.evaluate('Object.keys(S.bh).length')==10 and await pg.evaluate('S.wrong.filter(w=>w.b).length')==4
        await pg.click('#bankRetryWrong'); await pg.wait_for_timeout(300); assert await pg.evaluate('bs.items.length')==4
        for i in range(4):
            ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.click(f'[data-ox="{ans}"]'); await pg.wait_for_timeout(120); await pg.click('#bankNext'); await pg.wait_for_timeout(120)
        assert await pg.evaluate('S.wrong.filter(w=>w.b && !w.cleared).length')==0, '오답 정리 실패'
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(200)
        await pg.select_option('#bankLesson','1304'); await pg.wait_for_timeout(200); await pg.click('[data-bsel="type"][data-val="mc"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.click(f'[data-bp="{ans}"]'); await pg.wait_for_timeout(150); assert '맞혔습니다' in await pg.locator('.verdict').inner_text(); await pg.screenshot(path=f'{SC}/b4_mc.png', full_page=True)
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('[data-bsel="type"][data-val="blank"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.fill('#blankIn', ans); await pg.click('#blankGo'); await pg.wait_for_timeout(150); assert '맞혔습니다' in await pg.locator('.verdict').inner_text()
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('[data-bsel="type"][data-val="multi"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300); assert await pg.locator('.bogi').count()==1
        if await pg.locator('.qfig').count(): await pg.click('.qfig'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.screenshot(path=f'{SC}/b5_zoom.png'); await pg.click('#fvClose')
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('[data-bsel="type"][data-val="essay"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        await pg.fill('#essayIn','충돌 시간이 길어져 힘이 작아진다'); await pg.click('#essayShow'); await pg.wait_for_timeout(200); assert '모범 답안' in await pg.locator('.verdict').inner_text(); await pg.screenshot(path=f'{SC}/b6_essay.png', full_page=True)
        await pg.click('[data-ess="맞음"]'); await pg.wait_for_timeout(200); assert await pg.evaluate('S.stats.c')>=7
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('[data-lab="1304"]'); await pg.wait_for_timeout(400); t = await pg.locator('#v-lab').inner_text(); assert '해석의 3단계' in t and '직접 해보기' in t; await pg.screenshot(path=f'{SC}/b7_lab.png', full_page=True)
        await pg.click('[data-zoomlab]'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.click('#fvClose')
        await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(400); await pg.click('[data-zoom]'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.click('#fvPlus'); await pg.click('#fvClose')
        await pg.click('.tab[data-v="list"]'); await pg.wait_for_timeout(300); i = await pg.evaluate("CONCEPTS.findIndex(c=>c.id==='1304-05')"); await pg.click(f'.row[data-i="{i}"]'); await pg.wait_for_timeout(400)
        assert await pg.locator('#v-detail [data-lab="1304"]').count()==1 and await pg.locator('#v-detail [data-drill="1304"]').count()==1
        await pg.click('#v-detail [data-drill="1304"]'); await pg.wait_for_timeout(300); assert await pg.evaluate('bs && bs.items.every(q=>q.lessonId==="1304")')
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#goStats'); await pg.wait_for_timeout(800); assert '문제 은행 · 소단원별 정답률' in await pg.locator('#v-stats').inner_text()
        await b.close(); print('BANK OK', errs); assert not errs
asyncio.run(main())