#!/usr/bin/env python3
"""첫 실행 E2E — 소개 3장 → 시작 화면 → 단계별 가입(누구 → 약관·나이 → 계정 → 내 정보 → 학원 코드) → 환영 → 홈.
단계마다 막혀야 할 것이 막히는지, 이전으로 가도 적은 값이 남는지, 개인정보 고지 4가지가 보이는지 본다.

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_onboard.py [--shots 폴더]
"""
import asyncio, sys, os
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from _ui import auto_yes
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_onboard'; os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2); s = await ctx.new_page()
        s.on('pageerror', lambda e: errs.append(str(e)))
        s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
        shot = lambda n: s.screenshot(path=f'{SC}/{n}.png')
        err = lambda: s.locator('.auth .err').inner_text()
        await s.goto(APP); await s.wait_for_timeout(700)
        # ① 첫 실행: 소개 3장
        assert await s.evaluate('authMode') == 'intro', '첫 실행인데 소개가 안 나옴'
        for i in range(3):
            await shot(f'o0{i+1}_intro'); await s.click('#introNext'); await s.wait_for_timeout(250)
        assert await s.evaluate('authMode') == 'start' and await s.evaluate('S.introSeen') is True
        await shot('o04_start')
        await s.reload(); await s.wait_for_timeout(600); assert await s.evaluate('authMode') == 'start', '소개를 봤는데 또 나옴'
        # ② 1단계 누구세요
        await s.click('#goSignup'); await s.wait_for_timeout(200)
        assert '1 / 5' in await s.locator('.stepbar').inner_text(); await shot('o05_role')
        await s.click('[data-role="student"]'); await s.click('#suNext'); await s.wait_for_timeout(200)
        # ③ 2단계 약관: 나이·필수 동의 없으면 못 넘어감 · 개인정보 고지 4가지
        await s.click('#suNext'); assert '나이' in await err()
        await s.check('input[name=suAge][value="u14"]'); await s.wait_for_timeout(150)
        await s.click('#suNext'); assert '필수 약관' in await err()
        await s.click('#pvToggle'); await s.wait_for_timeout(150); pv = await s.locator('.pv').inner_text()
        assert all(k in pv for k in ('목적', '항목', '보유 기간', '동의하지 않을 권리')) and '보호자 성함' in pv, pv
        await s.click('#agTerms'); await s.wait_for_timeout(120)
        assert await s.is_checked('#agAll') is False, '하나만 골랐는데 전체 동의가 켜짐'
        await s.click('.agrees [data-legal="terms"]'); await s.wait_for_timeout(250); assert '이용약관' in await s.locator('.sheet h3').inner_text(); await s.click('#sheetClose')
        await s.check('#agAll'); await s.wait_for_timeout(120)
        assert await s.is_checked('#agTerms') and await s.is_checked('#agPrivacy'); await shot('o06_terms')
        await s.click('#suNext'); await s.wait_for_timeout(200)
        # ④ 3단계 계정: 이메일·비밀번호 확인, 보기 전환, 규칙 표시
        assert '3 / 5' in await s.locator('.stepbar').inner_text()
        await s.fill('#suEmail', 'bad'); await s.fill('#suPw', '12'); await s.click('#suNext'); assert '이메일' in await err()
        await s.fill('#suEmail', 'first@t.kr'); await s.click('#suNext'); assert '8자' in await err()
        await s.fill('#suPw', 'abc12345'); await s.wait_for_timeout(80)
        assert (await s.locator('.rules .ok').count()) == 2
        await s.click('#pwEye'); await s.wait_for_timeout(100); assert await s.get_attribute('#suPw', 'type') == 'text'
        await shot('o07_account'); await s.click('#suNext'); await s.wait_for_timeout(200)
        # ⑤ 이전으로 갔다 와도 값이 남는다
        await s.click('#suPrev'); await s.wait_for_timeout(150); assert await s.input_value('#suEmail') == 'first@t.kr' and await s.input_value('#suPw') == 'abc12345'
        await s.click('#suNext'); await s.wait_for_timeout(150)
        # ⑥ 4단계 내 정보: 만 14세 미만이라 보호자 정보 필수
        await s.fill('#suName', '첫학생'); await s.click('#suNext'); assert '보호자' in await err()
        await s.fill('#suGName', '첫보호'); await s.fill('#suGPhone', '010-2222-3333'); await shot('o08_info'); await s.click('#suNext'); await s.wait_for_timeout(200)
        # ⑦ 5단계 학원 코드: 틀린 코드는 알려 주되 가입은 된다(나중에 등록 가능)
        assert '5 / 5' in await s.locator('.stepbar').inner_text(); await shot('o09_code')
        await s.fill('#suCode', 'MON123'); await s.click('#suGo'); await s.wait_for_timeout(1100)
        # ⑧ 환영 → 홈
        assert await s.evaluate('authMode') == 'welcome' and '첫학생님, 준비됐어요' in await s.locator('h1').inner_text()
        await shot('o10_welcome'); await s.click('#welcomeGo'); await s.wait_for_timeout(900)
        assert await s.evaluate('view') == 'today' and await s.evaluate('S.auth && S.auth.code') == 'MON123'
        assert await s.evaluate('ACC.under14') is True and await s.evaluate('consentPending()') is True
        # ⑨ 원장 가입은 4단계에서 끝(학원 코드 단계 없음) · 보호자는 5단계에서 자녀 코드
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await auto_yes(s); await s.click('#logout'); await s.wait_for_timeout(600)
        await s.click('#goSignup'); await s.click('[data-role="owner"]'); await s.click('#suNext'); await s.wait_for_timeout(150)
        assert '2 / 4' in await s.locator('.stepbar').inner_text() and await s.locator('input[name=suAge]').count() == 0, '원장에게 나이를 묻거나 단계 수가 틀림'
        await s.click('#suPrev'); await s.click('#suPrev'); await s.wait_for_timeout(150); assert await s.evaluate('authMode') == 'start'
        # ⑩ 이미 가입한 이메일이면 계정 단계로 돌아가 알려 준다
        await s.click('#goSignup'); await s.click('[data-role="student"]'); await s.click('#suNext'); await s.check('input[name=suAge][value="14+"]'); await s.check('#agAll'); await s.click('#suNext')
        await s.fill('#suEmail', 'first@t.kr'); await s.fill('#suPw', 'abc12345'); await s.click('#suNext'); await s.fill('#suName', '또가입'); await s.click('#suNext'); await s.click('#suSkipCode'); await s.wait_for_timeout(900)
        assert '이미 가입' in await err() and '3 / 5' in await s.locator('.stepbar').inner_text()
        assert not errs, errs
        print('ONBOARD E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
