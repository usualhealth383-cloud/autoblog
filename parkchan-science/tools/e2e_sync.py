#!/usr/bin/env python3
"""기기 두 대 E2E — 같은 계정으로 폰(A)·태블릿(B)을 번갈아 쓸 때 기록이 사라지거나 지운 것이 되살아나지 않는가.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_sync.py
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'


async def main():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        async def device():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
            await pg.goto(APP); await pg.wait_for_timeout(600); return pg
        async def resume(pg):   # 앱으로 돌아옴(다른 앱 갔다 옴)
            await pg.evaluate("lastPull = 0; document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(900)
        A = await device()
        await signup(A, '두기기', 'two@t.kr')
        B = await device()
        await B.click('#goLogin'); await B.fill('#lgEmail', 'two@t.kr'); await B.fill('#lgPw', '123456'); await B.click('#lgGo'); await B.wait_for_timeout(1200)
        # ① A 에서 북마크 → B 로 돌아오면 보인다
        await A.click('#v-today [data-bm]'); await A.wait_for_timeout(1600)
        await resume(B); assert await B.evaluate('S.bm.length') == 1, 'A 의 북마크가 B 에 안 옴'
        # ② B 에서 그 북마크를 지움 → A 로 돌아오면 사라지고, A 가 다른 걸 저장해도 되살아나지 않는다
        await B.click('#v-today [data-bm]'); await B.wait_for_timeout(1600); assert await B.evaluate('S.bm.length') == 0
        await resume(A); assert await A.evaluate('S.bm.length') == 0, 'B 에서 지운 북마크가 A 에 남음'
        await A.click('#goQuiz'); await A.wait_for_timeout(300); ans = await A.evaluate('qState.q.answer'); await A.click(f'.opt[data-p="{ans}"]'); await A.wait_for_timeout(1700)
        await resume(B); assert await B.evaluate('S.bm.length') == 0, '지운 북마크가 되살아남'
        assert await B.evaluate('S.stats.a') == 1 and await B.evaluate('S.done.length') == 1, 'A 에서 푼 문제가 B 에 안 옴'
        # ③ B 가 하루 종일 켜져 있다가 저장해도 A 의 기록을 지우지 않는다(돌아올 때 먼저 받아 합침)
        await B.evaluate("S.sched.ddays.push({ id:'dd1', title:'중간고사', date:'2099-10-20' }); save(S)"); await B.wait_for_timeout(1600)
        await resume(A); assert await A.evaluate('S.sched.ddays.length') == 1 and await A.evaluate('S.stats.a') == 1
        await A.evaluate("S.sched.ddays = []; save(S)"); await A.wait_for_timeout(1600)
        await resume(B); assert await B.evaluate('S.sched.ddays.length') == 0, 'A 에서 지운 D-day 가 B 에 남음'
        assert await B.evaluate('S.stats.a') == 1 and await B.evaluate('S.done.length') == 1
        # 서버 최종 상태
        srv = await B.evaluate("DBX.loadProgress(progressKey())")
        assert srv['bm'] == [] and srv['sched']['ddays'] == [] and srv['stats']['a'] == 1, srv
        assert not errs, errs
        print('SYNC E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
