#!/usr/bin/env python3
"""회귀 E2E — 출시 전 점검에서 찾은 진도·접근 버그가 다시 생기지 않는지 본다.

1) 켤 때마다 푼 문제 수가 두 배로 늘던 버그   2) 로그아웃 뒤 다른 계정에 앞 사람 진도가 섞이던 버그
3) 수강 만료·원장 해제 뒤에도 전 범위가 열려 있던 버그   4) 계정 삭제 뒤 일정 화면이 멈추던 버그

전제: docs/parkchan 이 http://127.0.0.1:8765 에 떠 있다.   사용: python3 tools/e2e_regress.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_regress'; os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820})
        s = await ctx.new_page()
        s.on('pageerror', lambda e: errs.append(str(e)))
        s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
        s.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await s.goto(APP); await s.wait_for_timeout(400)
        async def login(em, pw):
            await s.click('#goLogin'); await s.fill('#lgEmail', em); await s.fill('#lgPw', pw); await s.click('#lgGo'); await s.wait_for_timeout(600)
        async def logout():
            await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); await s.click('#logout'); await s.wait_for_timeout(400)

        # 1) 통계가 켤 때마다 두 배가 되지 않는다
        await login('student@demo.kr', '1234')
        assert await s.evaluate('S.auth && S.auth.code') == 'MON123'
        await s.click('#goQuiz'); await s.wait_for_timeout(300); ans = await s.evaluate('qState.q.answer')
        await s.click(f'.opt[data-p="{ans}"]'); await s.wait_for_timeout(1500)       # 서버(로컬 DB) 저장 1초 디바운스
        assert await s.evaluate('S.stats.a') == 1
        for _ in range(3):
            await s.reload(); await s.wait_for_timeout(900)
        a = await s.evaluate('S.stats.a'); assert a == 1, f'다시 켤 때마다 문제 수가 늘어남: {a}'

        # 2) 로그아웃 → 다른 계정: 앞 사람 진도가 섞이지 않는다 · 다시 로그인하면 돌아온다
        await logout()
        assert await s.evaluate('S.done.length') == 0 and await s.evaluate('S.stats.a') == 0, '로그아웃했는데 진도가 남음'
        await s.click('#goSignup'); await s.fill('#suName', '둘째'); await s.fill('#suEmail', 'second@test.kr'); await s.fill('#suPw', '123456'); await s.check('#suAgree')
        await s.click('#suGo'); await s.wait_for_timeout(600)
        assert await s.evaluate('S.done.length') == 0 and await s.evaluate('S.stats.a') == 0, '다른 계정에 앞 사람 진도가 섞임'
        await logout(); await login('student@demo.kr', '1234')
        assert await s.evaluate('S.done.length') == 1 and await s.evaluate('S.stats.a') == 1, '다시 로그인했는데 진도가 돌아오지 않음'

        # 3) 수강 만료 → 켜면 닫힌다 / 원장이 해제 → 켜면 닫힌다
        await s.evaluate("""() => { const d = JSON.parse(localStorage.getItem('pcs.db.v2')); d.students.find(x=>x.code==='MON123').until = '2020-01-01'; localStorage.setItem('pcs.db.v2', JSON.stringify(d)); }""")
        await s.reload(); await s.wait_for_timeout(900)
        assert await s.evaluate('S.auth') is None and await s.evaluate('fullAccess()') is False, '수강이 끝났는데 전 범위가 열려 있음'
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300); assert await s.locator('.row.locked').count() > 100
        await s.evaluate("""() => { const d = JSON.parse(localStorage.getItem('pcs.db.v2')); d.students.find(x=>x.code==='MON123').until = '2099-01-01'; localStorage.setItem('pcs.db.v2', JSON.stringify(d)); }""")
        await s.reload(); await s.wait_for_timeout(900); assert await s.evaluate('S.auth && S.auth.code') == 'MON123', '기간을 늘렸는데 다시 열리지 않음'
        await s.evaluate("""() => { const d = JSON.parse(localStorage.getItem('pcs.db.v2')); d.students = d.students.filter(x=>x.code!=='MON123'); localStorage.setItem('pcs.db.v2', JSON.stringify(d)); }""")
        await s.reload(); await s.wait_for_timeout(900); assert await s.evaluate('S.auth') is None, '원장이 해제했는데 열려 있음'
        # 만료일이 지난 저장값은 연결이 끊겨도 열지 않는다
        await s.evaluate("() => { S.auth = { code:'X', cls:'월목반', until:'2020-01-01' }; }")
        assert await s.evaluate('fullAccess()') is False

        # 4) 계정 삭제 뒤 둘러보기 → 일정 화면이 멀쩡하다
        await logout(); await login('second@test.kr', '123456')
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); await s.click('#delAccount'); await s.wait_for_timeout(500)
        assert await s.evaluate('view') == 'auth'
        await s.click('#goGuest'); await s.wait_for_timeout(300); await s.click('.tab[data-v="plan"]'); await s.wait_for_timeout(400)
        assert await s.evaluate('view') == 'plan'; await s.screenshot(path=f'{SC}/r01_plan_after_delete.png')
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(300)

        assert not errs, errs
        print('REGRESS E2E OK · 콘솔 오류', errs)
        await b.close()

asyncio.run(main())
