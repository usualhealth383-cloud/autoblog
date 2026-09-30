#!/usr/bin/env python3
"""메일 링크 E2E — 운영처럼 '가입 확인 메일'을 요구할 때와 비밀번호 재설정 메일을 끝까지 따라가 본다(진짜 Postgres·PostgREST 시험대).

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 로 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_authmail.py [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_authmail'; os.makedirs(SC, exist_ok=True)
post = lambda path: U.urlopen(U.Request(GW + path, method='POST')).read()
mails = lambda: json.loads(U.urlopen(GW + '/__mail').read())


async def main():
    post('/__reset'); U.urlopen(GW + '/__autoconfirm?on=0').read()
    # 원장이 학생 코드를 하나 만들어 둔다(API 로)
    tok = json.loads(U.urlopen(U.Request(GW + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json'}, method='POST')).read())['access_token']
    U.urlopen(U.Request(GW + '/rest/v1/students', data=json.dumps({'code': 'MAIL01', 'name': '메일학생', 'cls': '화금반', 'until': '2099-01-01'}).encode(), headers={'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + tok}, method='POST')).read()
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); s = await ctx.new_page()
            s.on('pageerror', lambda e: errs.append(str(e)))
            s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await s.goto(APP); await s.wait_for_timeout(600)
            # 1) 가입 → '메일을 보냈습니다' 안내 → 인증 전 로그인은 한국어로 막힘
            await signup(s, '메일학생', 'mail@test.kr', code='MAIL01', welcome=False, wait=900)
            assert await s.evaluate('authMode') == 'login' and '메일' in await s.locator('.auth .info').inner_text(), '가입 확인 안내가 없다'
            assert await s.input_value('#lgEmail') == 'mail@test.kr'; await s.screenshot(path=f'{SC}/m01_mail_sent.png')
            await s.fill('#lgPw', '123456'); await s.click('#lgGo'); await s.wait_for_timeout(600)
            assert '메일 인증이 아직' in await s.locator('.auth .err').inner_text(), await s.locator('.auth .err').inner_text()
            # 2) 메일 링크 → 앱으로 돌아와 바로 로그인 · 적어 둔 학원 코드가 연결됨
            link = [m for m in mails() if m['type'] == 'signup'][-1]['link'].replace('redirect_to=', 'redirect_to=')
            await s.goto(link); await s.locator('#askMsg').wait_for(timeout=4000)
            assert 'mail@test.kr 계정으로 로그인합니다' in await s.inner_text('#askMsg'), '링크의 계정을 먼저 보여 주지 않음(로그인 바꿔치기 방지)'
            await s.screenshot(path=f'{SC}/m01b_link_confirm.png'); await s.click('#askYes'); await s.wait_for_timeout(1500)
            assert await s.evaluate('view') == 'today' and await s.evaluate('ACC && ACC.email') == 'mail@test.kr', await s.evaluate('view')
            assert await s.evaluate('S.auth && S.auth.code') == 'MAIL01', '인증 뒤 학원 코드가 연결되지 않았다'
            assert 'access_token' not in s.url, '주소창에 토큰이 남았다'; await s.screenshot(path=f'{SC}/m02_confirmed.png')
            # 3) 로그아웃 → 비밀번호 재설정 메일 → 새 비밀번호 → 새 비밀번호로 로그인
            await s.click('.tab[data-v="me"]'); await auto_yes(s); await s.click('#logout'); await s.wait_for_timeout(600)
            await s.click('#goLogin'); await s.click('#goForgot'); await s.fill('#fgEmail', 'mail@test.kr'); await s.click('#fgGo'); await s.wait_for_timeout(700)
            assert '재설정 메일' in await s.locator('.auth .info').inner_text()
            link = [m for m in mails() if m['type'] == 'recovery'][-1]['link']
            await s.add_init_script("Object.defineProperty(window, '__askManual', { get: () => sessionStorage.getItem('askManual') === '1', configurable: true })")
            await s.evaluate("sessionStorage.setItem('askManual', '1')")   # 이 링크에서는 확인 창을 사람처럼 직접 누른다
            await s.goto(link); await s.locator('#askMsg').wait_for(timeout=4000)
            assert '비밀번호를 새로 정합니다' in await s.inner_text('#askMsg'); await s.click('#askNo'); await s.wait_for_timeout(700)
            assert await s.evaluate('ACC') is None and await s.evaluate('authMode') != 'newpw' and '로그인하지 않았습니다' in await s.locator('.auth .err').inner_text(), '내 계정이 아니라고 했는데 로그인됨'
            await s.goto(link); await s.locator('#askMsg').wait_for(timeout=4000); await s.click('#askYes'); await s.wait_for_timeout(1300)
            await s.evaluate("sessionStorage.removeItem('askManual')")
            assert await s.evaluate('authMode') == 'newpw' and await s.locator('#npPw').count() == 1, '새 비밀번호 화면이 안 뜬다'
            await s.fill('#npPw', 'newpass1'); await s.fill('#npPw2', 'newpass2'); await s.click('#npGo'); await s.wait_for_timeout(300)
            assert '다릅니다' in await s.locator('.auth .err').inner_text(); await s.screenshot(path=f'{SC}/m03_newpw.png')
            await s.fill('#npPw', 'newpass1'); await s.fill('#npPw2', 'newpass1'); await s.click('#npGo'); await s.wait_for_timeout(1000)
            assert await s.evaluate('view') == 'today'
            await s.click('.tab[data-v="me"]'); await s.click('#logout'); await s.wait_for_timeout(600)
            await s.click('#goLogin'); await s.fill('#lgEmail', 'mail@test.kr'); await s.fill('#lgPw', '123456'); await s.click('#lgGo'); await s.wait_for_timeout(600)
            assert '다릅니다' in await s.locator('.auth .err').inner_text(), '옛 비밀번호로 로그인됨'
            await s.fill('#lgPw', 'newpass1'); await s.click('#lgGo'); await s.wait_for_timeout(900)
            assert await s.evaluate('view') == 'today' and await s.evaluate('S.auth && S.auth.code') == 'MAIL01'
            # 4) 쓴 링크를 다시 누르면 '만료' 안내
            await s.goto(link)
            await s.locator('.toast', has_text='만료').wait_for(timeout=4000)
            assert await s.evaluate('view') == 'today', '로그인 중 만료 링크: 알림만 떠야 한다'
            await s.click('.tab[data-v="me"]'); await s.click('#logout'); await s.wait_for_timeout(600)
            await s.goto(link); await s.wait_for_timeout(1000)
            assert await s.evaluate('authMode') == 'login' and '만료' in await s.locator('.auth .err').inner_text(), '로그아웃 상태 만료 링크: 로그인 화면에 이유가 떠야 한다'
            await s.screenshot(path=f'{SC}/m04_expired.png')
            assert not errs, errs
            print('AUTH MAIL E2E OK · 콘솔 오류', errs); await b.close()
    finally:
        U.urlopen(GW + '/__autoconfirm?on=1').read()

asyncio.run(main())
