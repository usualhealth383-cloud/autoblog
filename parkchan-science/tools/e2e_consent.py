#!/usr/bin/env python3
"""만 14세 미만 보호자 동의 E2E — 아이 가입 → 조용한 안내 카드(이야기·진도 저장만 잠김) → 보호자에게 링크 →
보호자 폰에서 동의 페이지 → 원장이 번호 대조 후 확인 문자 → 아이 앱이 열림 → 서면 동의도. 진짜 Postgres·PostgREST 시험대.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_consent.py [--shots 폴더]
"""
import asyncio, sys, os, json, re, urllib.request as U
from urllib.parse import unquote
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes, member
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']; SERVICE = json.loads(U.urlopen(GW + '/__anon').read())['service']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_consent'; os.makedirs(SC, exist_ok=True)
svc = lambda path: json.loads(U.urlopen(U.Request(GW + '/rest/v1/' + path, headers={'apikey': ANON, 'Authorization': 'Bearer ' + SERVICE})).read())


async def main():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        async def page():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(pg); return ctx, pg
        # ① 아이 가입(만 14세 미만)
        kc, k = await page(); await k.goto(APP); await k.wait_for_timeout(700)
        await signup(k, '어린이', 'kid@t.kr', u14=True, gname='김보호', gphone='010-1111-2222')
        assert await k.evaluate('view') == 'today' and await k.evaluate('consentPending()') is True
        assert await k.locator('#v-today .consent').count() == 1, '홈에 동의 안내가 없다'
        assert await k.locator('#goQuiz').count() == 1, '동의 전에도 오늘의 문제는 풀 수 있어야 한다'
        await k.screenshot(path=f'{SC}/c01_kid_today.png')
        # 교재·문제는 된다 / 진도는 서버에 안 올라간다
        await k.click('#goQuiz'); await k.wait_for_timeout(300); ans = await k.evaluate('qState.q.answer'); await k.click(f'.opt[data-p="{ans}"]'); await k.wait_for_timeout(1600)
        assert await k.evaluate('S.stats.a') == 1 and svc('progress?select=code') == [], '동의 전인데 진도가 서버에 올라감'
        # 이야기는 안내만
        await k.click('#backToday'); await k.wait_for_timeout(200)   # 풀이 중엔 탭 바가 없다(집중 모드) — 그만 풀기로
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
        # ④ 아이 앱: 보호자가 동의를 표시했지만, 학원이 보호자 번호로 확인 문자를 보내야 열린다(아이가 자기 번호를 적었을 수 있어서)
        await k.reload(); await k.wait_for_timeout(1300)
        assert await k.evaluate('consentPending()') is True, '확인 문자 전에 열림'
        ct = await k.locator('#v-today .consent').first.inner_text(); assert '보호자가 동의했어요' in ct and '확인 문자' in ct, ct
        await k.screenshot(path=f'{SC}/c05b_kid_given.png')
        assert svc('progress?select=code') == [], '확인 문자 전인데 진도가 서버에 올라감'
        # ⑤ 원장: 보호자 동의 표시 → 번호 대조 → 확인 문자 → 열림 / 다른 아이는 서면 동의
        k2c, k2 = await page(); await k2.goto(APP); await k2.wait_for_timeout(600)
        await signup(k2, '둘째아이', 'kid2@t.kr', u14=True, gname='이보호', gphone='01033334444')
        oc, o = await page(); await o.goto(APP); await o.wait_for_timeout(600)
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(1200)
        box = o.locator('#v-admin #consentBox').first; t = await box.inner_text()
        assert '보호자 동의 확인' in t and '2건 할 일' in t and '보호자 동의 표시' in t and '동의 대기' in t and '등록 서류' in t, t[:400]
        await o.screenshot(path=f'{SC}/c06_owner_list.png', full_page=True)
        assert await o.locator('a[data-cnotify]').count() == 1, '확인 문자 버튼이 동의 표시한 아이에게만 있어야 한다'
        sms = await o.locator('a[data-cnotify]').get_attribute('href'); assert re.sub(r'[^0-9]', '', sms.split('?')[0]) == '01011112222' and '동의를 확인했습니다' in unquote(sms), sms
        await o.evaluate("document.querySelector('a[data-cnotify]').removeAttribute('href')")   # 시험에서는 문자 앱을 열지 않는다
        await o.click('a[data-cnotify]'); await o.wait_for_timeout(1200)
        await o.click('[data-cpaper]'); await o.wait_for_timeout(1200)
        t = await o.locator('#v-admin #consentBox').first.text_content()
        assert await o.locator('#v-admin #consentBox').first.get_attribute('open') is None, '할 일이 없으면 접혀 있어야 한다'
        assert '할 일' not in t and t.count('동의 확인 완료') == 2 and '서면 동의 확인 완료' in t and '웹 동의 확인 완료' in t, t[:300]
        # 첫째 아이 앱: 이제 열림 · 진도가 서버에 올라감
        await k.reload(); await k.wait_for_timeout(1300)
        assert await k.evaluate('consentPending()') is False and await k.locator('.consent').count() == 0
        await member(k)   # 이야기 쓰기는 학원 코드·이용권 계정만(docs/11 §12-9) — 동의 잠금이 풀렸는지만 본다
        await k.click('.tab[data-v="talk"]'); await k.wait_for_timeout(600); assert await k.locator('#postNew').count() == 1, '확인 문자 뒤에도 이야기가 잠김'
        kkey = await k.evaluate('progressKey()'); await k.evaluate('save(S)'); await k.wait_for_timeout(1600)
        assert kkey and kkey in [x['code'] for x in svc('progress?select=code')], '동의 뒤 진도가 서버에 안 올라감'
        await k2.reload(); await k2.wait_for_timeout(1200); assert await k2.evaluate('consentPending()') is False, '서면 동의 뒤에도 잠김'
        # ⑤-2 번호가 등록 서류와 다름 → 원장이 '번호가 달라요' → 아이가 번호를 고쳐 다시 요청
        k3c, k3 = await page(); await k3.goto(APP); await k3.wait_for_timeout(600)
        await signup(k3, '셋째아이', 'kid3@t.kr', u14=True, gname='최보호', gphone='01012345678')
        await k3.click('#v-today #consentSend'); await k3.wait_for_timeout(700)
        l3 = re.search(r'https?://\S+consent\.html\?t=[0-9a-f]{36}', unquote(await k3.locator('.sheet a.btn').first.get_attribute('href'))).group(0); await k3.click('#sheetClose')
        await g.goto(l3); await g.wait_for_timeout(800); await g.fill('#gName', '최보호'); await g.check('#gAgree'); await g.click('#gGo'); await g.wait_for_timeout(900)
        await o.reload(); await o.wait_for_timeout(1300)
        await o.click('[data-creset]'); await o.wait_for_timeout(1200)
        t = await o.locator('#v-admin #consentBox').first.inner_text(); assert '번호 다시 받는 중' in t and await o.locator('[data-cnotify]').count() == 0, t[:300]
        await k3.reload(); await k3.wait_for_timeout(1300)
        ct = await k3.locator('#v-today .consent').first.inner_text(); assert '번호를 다시 확인' in ct, ct
        await k3.screenshot(path=f'{SC}/c07_kid_reset.png')
        await k3.fill('#consentPhone', '123'); await k3.click('#v-today #consentSend'); await k3.wait_for_timeout(600)
        assert await k3.locator('.sheet').count() == 0, '틀린 번호로 요청이 나감'
        await k3.fill('#consentPhone', '010-9876-5432'); await k3.click('#v-today #consentSend'); await k3.wait_for_timeout(800)
        href = await k3.locator('.sheet a.btn').first.get_attribute('href'); assert re.sub(r'[^0-9]', '', href.split('?')[0]) == '01098765432', href
        await k3.click('#sheetClose')
        await o.reload(); await o.wait_for_timeout(1300); assert '01098765432' in re.sub(r'[^0-9]', '', await o.locator('#v-admin #consentBox').first.inner_text()), '원장 목록에 고친 번호가 안 보임'
        # ⑥ 로컬(시연) 모드: 같은 브라우저에서 동의 페이지가 기기 저장소를 읽고 쓴다
        lc, l = await page(); await l.goto('http://127.0.0.1:8765/index.html?server='); await l.wait_for_timeout(600)
        assert await l.evaluate('DBX.mode') == 'local'
        await signup(l, '시연아이', 'demo-kid@t.kr', u14=True, gname='박보호', gphone='01077778888')
        await l.click('#v-today #consentSend'); await l.wait_for_timeout(500)
        lk = re.search(r'https?://\S+consent\.html\?t=[0-9a-f]{36}', unquote(await l.locator('.sheet a.btn').first.get_attribute('href'))).group(0)
        await l.goto(lk); await l.wait_for_timeout(600); await l.fill('#gName', '박보호'); await l.check('#gAgree'); await l.click('#gGo'); await l.wait_for_timeout(500)
        assert '고맙습니다' in await l.locator('h1').inner_text()
        await l.goto('http://127.0.0.1:8765/index.html'); await l.wait_for_timeout(800); assert await l.evaluate('consentPending()') is True, '로컬 모드: 확인 문자 전에 열림'
        await l.evaluate("DBX.consentMark(ACC.id, 'notified')")   # 시연 모드에서 원장이 확인 문자를 보낸 셈
        await l.reload(); await l.wait_for_timeout(800); assert await l.evaluate('consentPending()') is False, '로컬 모드 동의가 반영 안 됨'
        assert not errs, errs
        print('CONSENT E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
