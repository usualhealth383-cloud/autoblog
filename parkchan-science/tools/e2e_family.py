#!/usr/bin/env python3
"""형제·자매 E2E — 보호자 한 계정에 자녀 둘을 잇고, 이름을 눌러 바꿔 보고, 한 명만 연결 해제한다.

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh 시험대(:8767)에 붙는다.
사용: python3 tools/e2e_family.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SRV = '--server' in sys.argv; GW = 'http://127.0.0.1:8767'
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={json.loads(U.urlopen(GW + '/__anon').read())['anon']}" if SRV else '?server=')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_family'; os.makedirs(SC, exist_ok=True)
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')


async def main():
    if SRV: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        await auto_yes(pg)
        await pg.goto(APP); await pg.wait_for_timeout(700)
        async def login(em, pw):
            await pg.click('#goLogin'); await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1000)
        async def logout():
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(700)
        # 원장: 형제 둘 등록 + 동생만 수동 출석
        await login(*OWNER); codes = []
        for nm, cls in (('형학생', '월목반'), ('동생학생', '화금반')):
            await pg.fill('#stName', nm); await pg.select_option('#stCls', cls); await pg.fill('#stUntil', '2099-12-31'); await pg.click('#stAdd'); await pg.wait_for_timeout(700)
            codes.append(await pg.evaluate('issued.code'))
        await pg.click('[data-adm="attend"]'); await pg.wait_for_timeout(900); await pg.click(f'[data-manual="{codes[1]}"]'); await pg.wait_for_timeout(800)
        await pg.click('[data-adm="sched"]'); await pg.wait_for_timeout(700); await pg.select_option('#scCls', '화금반'); await pg.fill('#scDate', '2099-10-15'); await pg.fill('#scT', '3단원 평가')
        await pg.click('#scSend'); await pg.wait_for_timeout(800)
        await logout()
        # 보호자: 형 코드로 가입 → 동생 추가
        await signup(pg, '형제보호자', 'fam@t.kr', role='parent', child=codes[0])
        assert await pg.evaluate('view') == 'parent' and '형학생 학생' in await pg.locator('#v-parent').inner_text()
        assert await pg.locator('[data-kid]').count() == 0, '자녀가 하나인데 고르기 칩이 보임'
        await pg.click('#childAdd'); await pg.wait_for_timeout(300)
        await pg.fill('.sheet #childIn', 'ZZZ999'); await pg.click('.sheet #childGo'); await pg.wait_for_timeout(600)
        assert '등록되지 않은' in await pg.locator('#childAddErr').inner_text(), '시트 안에 오류가 안 뜸'
        await pg.fill('.sheet #childIn', codes[1]); await pg.click('.sheet #childGo'); await pg.wait_for_timeout(1400)
        assert await pg.locator('#sheetBg').count() == 0 and await pg.locator('[data-kid]').count() == 2, '자녀 고르기 칩이 두 개가 아님'
        body = await pg.locator('#v-parent').inner_text(); assert '동생학생 학생' in body and '출석' in body, body[:200]
        await pg.screenshot(path=f'{SC}/f01_two_kids.png', full_page=True)
        await pg.click(f'[data-kid="{codes[0]}"]'); await pg.wait_for_timeout(900)
        body = await pg.locator('#v-parent').inner_text(); assert '형학생 학생' in body and '아직 출석 전' in body, body[:200]
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); assert '2명' in await pg.locator('#v-me').inner_text()
        # 보호자 일정 화면에 동생 반 일정이 이름과 함께
        await pg.evaluate("planDay = '2099-10-15'"); await pg.click('.tab[data-v="plan"]'); await pg.wait_for_timeout(900)
        assert await pg.evaluate("acadEvents.some(e => e.title === '동생학생 · 3단원 평가')"), await pg.evaluate('acadEvents')
        # 비밀번호 바꾸기 → 새 비밀번호로만 로그인
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#pwOpen')
        await pg.fill('#pwNew', 'newpw77'); await pg.fill('#pwNew2', 'newpw78'); await pg.click('#pwSave'); assert '다릅니다' in await pg.locator('#pwErr').inner_text()
        await pg.fill('#pwNew2', 'newpw77'); await pg.click('#pwSave'); await pg.wait_for_timeout(800); assert await pg.locator('#sheetBg').count() == 0
        await logout(); await login('fam@t.kr', '123456'); assert '다릅니다' in await pg.locator('.auth .err').inner_text(), '옛 비밀번호로 로그인됨'
        await pg.fill('#lgPw', 'newpw77'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200); assert await pg.evaluate('view') == 'parent'
        # 동생만 연결 해제 → 형만 남음
        await pg.click('.tab[data-v="parent"]'); await pg.wait_for_timeout(600); await pg.click(f'[data-kid="{codes[1]}"]'); await pg.wait_for_timeout(800)
        await pg.click('#unlinkChild'); await pg.wait_for_timeout(1000)
        assert await pg.locator('[data-kid]').count() == 0 and '형학생 학생' in await pg.locator('#v-parent').inner_text(), '한 명만 해제가 안 됨'
        assert await pg.evaluate('ACC.childCodes.length') == 1
        # 원장 학생 상세: 형에게 보호자 1명, 동생 0명
        await logout(); await login(*OWNER); await pg.click('[data-adm="students"]'); await pg.wait_for_timeout(700)
        await pg.click(f'[data-stu="{codes[0]}"]'); await pg.wait_for_timeout(800); assert '보호자 연결 1명' in await pg.locator('.sheet').inner_text(); await pg.click('#sheetClose')
        await pg.click(f'[data-stu="{codes[1]}"]'); await pg.wait_for_timeout(800); assert '보호자 연결 0명' in await pg.locator('.sheet').inner_text()
        assert not errs, errs
        print(('SERVER ' if SRV else 'LOCAL ') + 'FAMILY E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
