#!/usr/bin/env python3
"""서버 모드 E2E — 모의 Supabase(mock_server.py) 앞에서 앱의 서버 어댑터를 끝까지 돌려 본다.

전제: docs/parkchan 이 http://127.0.0.1:8765 에, mock_server.py 가 :8766 에 떠 있다.
검사: 원장 로그인 → 학생 등록(코드 발급) → 공지 발송 → [학생 기기] 코드 등록 → 공지 배너 → 출석(서버 코드) →
      문제 풀이(진도 서버 저장) → [새 기기] 같은 코드 등록 → 진도 이어짐 → [원장] 읽음 1·출석 1
"""
import asyncio, sys, json, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html?server=http://127.0.0.1:8766&key=anon'
SC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/e2e_server'
import os; os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        async def page():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}, device_scale_factor=2)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and 'status of 4' not in m.text else None)   # 4xx 는 일부러 낸 오류(틀린 비밀번호·없는 코드)
            await pg.goto(APP); await pg.wait_for_timeout(500)
            await pg.click('#onbGo'); await pg.wait_for_timeout(200)
            return ctx, pg
        shot = lambda pg, n: pg.screenshot(path=f'{SC}/{n}.png', full_page=True)

        urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766/__reset', method='POST')).read()
        # ── 원장 기기 ──
        octx, o = await page()
        assert await o.evaluate('DBX.mode') == 'server'
        await o.click('.tab[data-v="me"]'); await o.click('#adminOn')
        await o.fill('#ownEmail', 'owner@parkchan.kr'); await o.fill('#pinIn', 'wrong'); await o.click('#pinGo'); await o.wait_for_timeout(300)
        assert '다릅니다' in await o.locator('.err').inner_text(), '틀린 비밀번호가 통과됨'
        await o.fill('#ownEmail', 'owner@parkchan.kr'); await o.fill('#pinIn', 'owner-pass'); await o.click('#pinGo'); await o.wait_for_timeout(500)
        assert 'owner@parkchan.kr' in await o.locator('.adm-h .who').inner_text()
        await shot(o, 's01_owner_students')
        await o.fill('#stName', '서버학생'); await o.select_option('#stCls', '월목반'); await o.fill('#stPhone', '01099998888'); await o.click('#stAdd'); await o.wait_for_timeout(500)
        code = await o.evaluate('issued.code'); print('발급 코드', code)
        assert await o.locator('.stu').count() == 1
        await o.click('[data-adm="notice"]'); await o.wait_for_timeout(300)
        await o.click('[data-chip="휴강"]'); await o.fill('#ntD', '태풍으로 오늘 휴강'); await o.select_option('#ntCls', '월목반'); await o.click('#ntSend'); await o.wait_for_timeout(500)
        assert '읽음 0' in await o.locator('.sent .r').first.inner_text()
        await shot(o, 's02_owner_notice')
        await o.click('[data-adm="attend"]'); await o.wait_for_timeout(1500)
        att = await o.locator('#attV').inner_text(); assert att.isdigit() and len(att) == 4, f'서버 출석 코드 표시 실패: {att!r}'
        await shot(o, 's03_owner_attend')

        # ── 학생 기기 1 ──
        sctx, s = await page()
        await s.click('.tab[data-v="me"]'); await s.fill('#codeIn', 'ZZZ000'); await s.click('#codeGo'); await s.wait_for_timeout(400)
        assert '등록되지' in await s.locator('.err').inner_text()
        await s.fill('#codeIn', code); await s.click('#codeGo'); await s.wait_for_timeout(600)
        assert '서버학생' in await s.locator('.pass .who').inner_text()
        await shot(s, 's04_student_me')
        await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(600)
        assert await s.locator('.notice').count() == 1, '월목반 공지 배너 없음'
        await s.click('#attOpen'); await s.fill('#attIn', '0000'); await s.click('#attGo'); await s.wait_for_timeout(400)
        assert '맞지' in await s.locator('#attErr').inner_text()
        await s.fill('#attIn', att); await s.click('#attGo'); await s.wait_for_timeout(700)
        assert '출석' in await s.locator('.pill').first.inner_text(), '출석 표시 없음'
        await s.click('#okNotice'); await s.wait_for_timeout(500)
        assert await s.locator('.notice').count() == 0
        await shot(s, 's05_student_attended')
        # 문제 풀이 → 진도 서버 저장
        await s.click('#goQuiz'); await s.wait_for_timeout(300)
        ans = await s.evaluate('qState.q.answer'); wrong = 1 if ans != 1 else 2
        await s.click(f'.opt[data-p="{wrong}"]'); await s.wait_for_timeout(1800)   # 1.2초 디바운스 뒤 서버 저장
        done1 = await s.evaluate('S.done.length'); assert done1 == 1

        # ── 학생 기기 2 (새 폰) — 같은 코드로 등록하면 진도가 이어져야 ──
        s2ctx, s2 = await page()
        await s2.click('.tab[data-v="me"]'); await s2.fill('#codeIn', code); await s2.click('#codeGo'); await s2.wait_for_timeout(800)
        done2 = await s2.evaluate('S.done.length'); wrong2 = await s2.evaluate('S.wrong.length')
        assert done2 == 1 and wrong2 == 1, f'진도 동기화 실패 done={done2} wrong={wrong2}'
        assert '서버에 저장' in await s2.locator('#v-me .fine').inner_text()
        await shot(s2, 's06_student2_synced')

        # ── 원장: 읽음 1 · 출석 1 ──
        await o.click('[data-adm="notice"]'); await o.wait_for_timeout(500)
        assert '읽음 1' in await o.locator('.sent .r').first.inner_text(), '읽음 집계 실패'
        await o.click('[data-adm="attend"]'); await o.wait_for_timeout(1500)
        assert '1/1 출석' in await o.locator('.unit-h').first.inner_text()
        await shot(o, 's07_owner_after')
        # 원장 로그아웃 후에는 서버가 원장 요청을 거부해야
        await o.click('.tab[data-v="me"]'); await o.click('#adminOff'); await o.wait_for_timeout(200)
        assert await o.evaluate('OWNER') is None
        for c in (octx, sctx, s2ctx): await c.close()
        await b.close()
        print('SERVER E2E OK · 콘솔 오류', errs)
        assert not errs
asyncio.run(main())
