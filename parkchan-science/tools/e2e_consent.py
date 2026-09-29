#!/usr/bin/env python3
"""만 14세 미만 보호자 동의 E2E — 아이 가입 → 조용한 안내 카드(이야기·진도 저장만 잠김) → 보호자에게 링크 →
보호자 폰에서 동의 페이지 → 아이 앱이 열림 → 원장이 확인 문자 → 서면 동의도. 진짜 Postgres·PostgREST 시험대.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_consent.py [--shots 폴더]
"""
import asyncio, sys, os, json, re, urllib.request as U
from urllib.parse import unquote
from playwright.async_api import async_playwright
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']; SERVICE = json.loads(U.urlopen(GW + '/__anon').read())['service']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_consent'; os.makedirs(SC, exist_ok=True)
svc = lambda path: json.loads(U.urlopen(U.Request(GW + '/rest/v1/' + path, headers={'apikey': ANON, 'Authorization': 'Bearer ' + SERVICE})).read())


async def main():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        async def page():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            pg.on('dialog', lambda d: asyncio.ensure_future(d.accept())); return ctx, pg
        # ① 아이 가입(만 14세 미만)
        kc, k = await page(); await k.goto(APP); await k.wait_for_timeout(700)
        await k.click('#goSignup'); await k.fill('#suName', '어린이'); await k.fill('#suEmail', 'kid@t.kr'); await k.fill('#suPw', '123456')
        await k.select_option('#suAge', 'u14'); await k.wait_for_timeout(200)
        await k.fill('#suGName', '김보호'); await k.fill('#suGPhone', '010-1111-2222'); await k.check('#suAgree'); await k.click('#suGo'); await k.wait_for_timeout(1200)
        assert await k.evaluate('view') == 'today' and await k.evaluate('consentPending()') is True
        assert await k.locator('#v-today .consent').count() == 1, '홈에 동의 안내가 없다'
        assert await k.locator('#goQuiz').count() == 1, '동의 전에도 오늘의 문제는 풀 수 있어야 한다'
        await k.screenshot(path=f'{SC}/c01_kid_today.png')
        # 교재·문제는 된다 / 진도는 서버에 안 올라간다
        await k.click('#goQuiz'); await k.wait_for_timeout(300); ans = await k.evaluate('qState.q.answer'); await k.click(f'.opt[data-p="{ans}"]'); await k.wait_for_timeout(1600)
        assert await k.evaluate('S.stats.a') == 1 and svc('progress?select=code') == [], '동의 전인데 진도가 서버에 올라감'
        # 이야기는 안내만
        await k.click('.tab[data-v="talk"]'); await k.wait_for_timeout(500)
        assert await k.locator('#v-talk .consent').count() == 1 and await k.locator('#postNew').count() == 0; await k.screenshot(path=f'{SC}/c02_kid_talk.png')
        # ② 보호자에게 요청 → 문자 링크
        await k.click('#v-talk #consentSend'); await k.wait_for_timeout(700)
        href = await k.locator('.sheet a.btn').first.get_attribute('href'); assert re.sub(r'[^0-9]', '', href.split('?')[0]) == '01011112222', href
        link = re.search(r'https?://\S+consent\.html\?t=[0-9a-f]{36}', unquote(href)).group(0); print('  동의 링크:', link[:60] + '…')
        await k.screenshot(path=f'{SC}/c03_send_sheet.png'); await k.click('#sheetClose')
        # ③ 보호자 폰(다른 브라우저)에서 동의 — 운영에서는 빌드에 서버 주소가 심겨 있고, 시험대에서는 한 번 붙여 준다
        gc, g = await page(); await g.goto(APP); await g.wait_for_timeout(400); await g.goto(link); await g.wait_for_timeout(900)
        assert '어○○ 학생' in await g.locator('h1').inner_text(), await g.locator('h1').inner_text()
        await g.screenshot(path=f'{SC}/c04_guardian_page.png', full_page=True)
        await g.click('#gGo'); assert '성함' in await g.locator('#gErr').inner_text()
        await g.fill('#gName', '김보호'); await g.click('#gGo'); assert '동의 칸' in await g.locator('#gErr').inner_text()
        await g.check('#gAgree'); await g.click('#gGo'); await g.wait_for_timeout(900)
        assert '고맙습니다' in await g.locator('h1').inner_text(); await g.screenshot(path=f'{SC}/c05_guardian_done.png')
        await g.reload(); await g.wait_for_timeout(800); assert '고맙습니다' in await g.locator('h1').inner_text(), '다시 열면 완료 화면이어야 한다'
        # ④ 아이 앱: 다시 켜면 열림 · 진도가 서버에 올라감
        await k.reload(); await k.wait_for_timeout(1300)
        assert await k.evaluate('consentPending()') is False and await k.locator('.consent').count() == 0
        await k.click('.tab[data-v="talk"]'); await k.wait_for_timeout(600); assert await k.locator('#postNew').count() == 1, '동의 뒤에도 이야기가 잠김'
        await k.evaluate('save(S)'); await k.wait_for_timeout(1600); assert len(svc('progress?select=code')) == 1, '동의 뒤 진도가 서버에 안 올라감'
        # ⑤ 원장: 웹 동의 → 확인 문자 → 완료 / 다른 아이는 서면 동의
        k2c, k2 = await page(); await k2.goto(APP); await k2.wait_for_timeout(600)
        await k2.click('#goSignup'); await k2.fill('#suName', '둘째아이'); await k2.fill('#suEmail', 'kid2@t.kr'); await k2.fill('#suPw', '123456')
        await k2.select_option('#suAge', 'u14'); await k2.wait_for_timeout(200); await k2.fill('#suGName', '이보호'); await k2.fill('#suGPhone', '01033334444'); await k2.check('#suAgree'); await k2.click('#suGo'); await k2.wait_for_timeout(1100)
        oc, o = await page(); await o.goto(APP); await o.wait_for_timeout(600)
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(1200)
        box = o.locator('#v-admin #consentBox').first; t = await box.inner_text()
        assert '보호자 동의 확인' in t and '2건 할 일' in t and '웹 동의' in t and '동의 대기' in t, t[:300]
        await o.screenshot(path=f'{SC}/c06_owner_list.png', full_page=True)
        sms = await o.locator('a[data-cnotify]').get_attribute('href'); assert re.sub(r'[^0-9]', '', sms.split('?')[0]) == '01011112222' and '동의를 확인했습니다' in unquote(sms), sms
        await o.evaluate("document.querySelector('a[data-cnotify]').removeAttribute('href')")   # 시험에서는 문자 앱을 열지 않는다
        await o.click('a[data-cnotify]'); await o.wait_for_timeout(1200)
        await o.click('[data-cpaper]'); await o.wait_for_timeout(1200)
        t = await o.locator('#v-admin #consentBox').first.text_content()
        assert await o.locator('#v-admin #consentBox').first.get_attribute('open') is None, '할 일이 없으면 접혀 있어야 한다'
        assert '할 일' not in t and t.count('동의 확인 완료') == 2 and '서면 동의 확인 완료' in t, t[:300]
        await k2.reload(); await k2.wait_for_timeout(1200); assert await k2.evaluate('consentPending()') is False, '서면 동의 뒤에도 잠김'
        # ⑥ 로컬(시연) 모드: 같은 브라우저에서 동의 페이지가 기기 저장소를 읽고 쓴다
        lc, l = await page(); await l.goto('http://127.0.0.1:8765/index.html?server='); await l.wait_for_timeout(600)
        assert await l.evaluate('DBX.mode') == 'local'
        await l.click('#goSignup'); await l.fill('#suName', '시연아이'); await l.fill('#suEmail', 'demo-kid@t.kr'); await l.fill('#suPw', '123456')
        await l.select_option('#suAge', 'u14'); await l.wait_for_timeout(200); await l.fill('#suGName', '박보호'); await l.fill('#suGPhone', '01077778888'); await l.check('#suAgree'); await l.click('#suGo'); await l.wait_for_timeout(900)
        await l.click('#v-today #consentSend'); await l.wait_for_timeout(500)
        lk = re.search(r'https?://\S+consent\.html\?t=[0-9a-f]{36}', unquote(await l.locator('.sheet a.btn').first.get_attribute('href'))).group(0)
        await l.goto(lk); await l.wait_for_timeout(600); await l.fill('#gName', '박보호'); await l.check('#gAgree'); await l.click('#gGo'); await l.wait_for_timeout(500)
        assert '고맙습니다' in await l.locator('h1').inner_text()
        await l.goto('http://127.0.0.1:8765/index.html'); await l.wait_for_timeout(800); assert await l.evaluate('consentPending()') is False, '로컬 모드 동의가 반영 안 됨'
        assert not errs, errs
        print('CONSENT E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
