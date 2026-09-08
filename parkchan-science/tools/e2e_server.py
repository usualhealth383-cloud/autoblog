#!/usr/bin/env python3
"""서버 모드 E2E(v2) — 모의 Supabase(mock_server.py) 앞에서 계정·학생·보호자·원장·이용권 흐름을 돌려 본다.

전제: docs/parkchan 이 http://127.0.0.1:8765 에, mock_server.py 가 :8766 에 떠 있다.
"""
import asyncio, sys, os, urllib.request
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html?server=http://127.0.0.1:8766&key=anon'
SC = (sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else '/tmp/e2e_server')); os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        async def page():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}, device_scale_factor=2)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
            await pg.goto(APP); await pg.wait_for_timeout(600)
            return ctx, pg
        shot = lambda pg, n: pg.screenshot(path=f'{SC}/{n}.png', full_page=True)
        async def txt(pg, sel): return await pg.locator(sel).first.inner_text()
        urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766/__reset', method='POST')).read()

        # ── 원장: 로그인 → 학생 등록 → 공지 → 출석 코드 → 이용권 발급 ──
        octx, o = await page(); assert await o.evaluate('DBX.mode') == 'server'
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'nope'); await o.click('#lgGo'); await o.wait_for_timeout(400); assert '다릅니다' in await txt(o, '.err')
        await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(800)
        assert await o.evaluate('view') == 'admin' and 'owner@parkchan.kr' in await txt(o, '.adm-h .who')
        await o.fill('#stName', '서버학생'); await o.select_option('#stCls', '월목반'); await o.fill('#stPhone', '01099998888'); await o.click('#stAdd'); await o.wait_for_timeout(600)
        code = await o.evaluate('issued.code'); print('발급 코드', code); await shot(o, 's01_owner_students')
        await o.click('[data-adm="notice"]'); await o.wait_for_timeout(400); await o.click('[data-chip="휴강"]'); await o.fill('#ntD', '태풍으로 오늘 휴강'); await o.select_option('#ntCls', '월목반'); await o.click('#ntSend'); await o.wait_for_timeout(600)
        assert '읽음 0' in await txt(o, '.sent .r')
        await o.click('[data-adm="attend"]'); await o.wait_for_timeout(1500); att = await txt(o, '#attV'); assert att.isdigit() and len(att) == 4, att
        await o.click('[data-adm="settings"]'); await o.wait_for_timeout(600); await o.fill('#clsName', '일요반'); await o.click('#clsAdd'); await o.wait_for_timeout(500); assert '일요반' in await txt(o, '#v-admin')
        await o.select_option('#passDays', '30'); await o.click('#passIssue'); await o.wait_for_timeout(500); pcode = await o.evaluate('issuedPass.code'); await shot(o, 's02_owner_settings')

        # ── 학생: 가입(코드 포함) → 공지·출석 → 문제 → 진도 서버 저장 ──
        sctx, s = await page()
        await s.click('#goSignup'); await s.fill('#suName', '서버학생'); await s.fill('#suEmail', 'stu@srv.kr'); await s.fill('#suPw', '123456'); await s.fill('#suCode', code); await s.check('#suAgree'); await s.click('#suGo'); await s.wait_for_timeout(1200)
        assert await s.evaluate('view') == 'today' and await s.evaluate('S.auth && S.auth.cls') == '월목반', '학생 가입+코드 연결 실패'
        assert await s.locator('.notice').count() == 1, '공지 배너 없음'
        await s.click('#attOpen'); await s.fill('#attIn', '0000'); await s.click('#attGo'); await s.wait_for_timeout(500); assert '맞지' in await txt(s, '#attErr')
        await s.fill('#attIn', att); await s.click('#attGo'); await s.wait_for_timeout(900); assert '출석' in await txt(s, '.pill')
        await s.click('#okNotice'); await s.wait_for_timeout(600); assert await s.locator('.notice').count() == 0
        await s.click('[data-bm]'); await s.click('#goQuiz'); await s.wait_for_timeout(400); ans = await s.evaluate('qState.q.answer'); await s.click(f'.opt[data-p="{1 if ans != 1 else 2}"]'); await s.wait_for_timeout(1800)
        await shot(s, 's03_student_quiz')
        # 새 폰: 로그인만 하면 진도·북마크·코드가 따라온다
        s2ctx, s2 = await page()
        await s2.click('#goLogin'); await s2.fill('#lgEmail', 'stu@srv.kr'); await s2.fill('#lgPw', '123456'); await s2.click('#lgGo'); await s2.wait_for_timeout(1200)
        assert await s2.evaluate('S.auth && S.auth.code') == code and await s2.evaluate('S.done.length') == 1 and await s2.evaluate('S.wrong.length') == 1 and await s2.evaluate('S.bm.length') == 1, '새 기기 동기화 실패'
        await s2.click('.tab[data-v="stats"]'); await s2.wait_for_timeout(800); assert '학원 출석 1일' in await txt(s2, '.legend'); await shot(s2, 's04_student2_stats')

        # ── 보호자: 가입 → 자녀 연결 → 출석·공지·진도 보기 ──
        pctx, pr = await page()
        await pr.click('#goSignup'); await pr.click('[data-role="parent"]'); await pr.fill('#suName', '서버보호자'); await pr.fill('#suEmail', 'par@srv.kr'); await pr.fill('#suPw', '123456'); await pr.fill('#suChild', code); await pr.check('#suAgree'); await pr.click('#suGo'); await pr.wait_for_timeout(1500)
        assert await pr.evaluate('view') == 'parent'; body = await txt(pr, '#v-parent')
        assert '서버학생 학생' in body and '출석' in body and '휴강' in body and '개념 1개' in body, body[:300]; await shot(pr, 's05_parent')

        # ── 학원 밖 학생: 이용권 코드 ──
        gctx, g = await page()
        await g.click('#goSignup'); await g.fill('#suName', '외부'); await g.fill('#suEmail', 'out@srv.kr'); await g.fill('#suPw', '123456'); await g.check('#suAgree'); await g.click('#suGo'); await g.wait_for_timeout(1000)
        assert await g.evaluate('fullAccess()') is False
        await g.click('.tab[data-v="me"]'); await g.wait_for_timeout(300); await g.click('#goPlans'); await g.wait_for_timeout(400)
        await g.fill('#passIn', pcode); await g.click('#passGo'); await g.wait_for_timeout(800); assert await g.evaluate('fullAccess()') is True, '이용권 등록 실패'
        await g.fill('#passIn', pcode); await g.click('#passGo'); await g.wait_for_timeout(500); assert '이미' in await txt(g, '.err')
        # 게스트·타인은 서버에서 원장 자료를 못 본다 (RLS)
        r = await g.evaluate("api('/rest/v1/students?select=*').then(x=>x.length).catch(e=>'denied:'+e.status)"); assert r in (0, 'denied:401'), f'RLS 누수: {r}'
        # 계정 삭제 뒤 로그인 불가
        await g.click('.tab[data-v="me"]'); await g.wait_for_timeout(300); await g.click('#delAccount'); await g.wait_for_timeout(800); assert await g.evaluate('view') == 'auth'
        await g.click('#goLogin'); await g.fill('#lgEmail', 'out@srv.kr'); await g.fill('#lgPw', '123456'); await g.click('#lgGo'); await g.wait_for_timeout(500); assert '다릅니다' in await txt(g, '.err')

        # ── 원장: 읽음 1 · 출석 1 · 학생 상세에 보호자 1명 · 통계 ──
        await o.click('[data-adm="notice"]'); await o.wait_for_timeout(700); assert '읽음 1' in await txt(o, '.sent .r'), '읽음 집계 실패'
        await o.click('[data-adm="students"]'); await o.wait_for_timeout(500); await o.click(f'[data-stu="{code}"]'); await o.wait_for_timeout(800); sh = await txt(o, '.sheet'); assert '보호자 연결 1명' in sh and '공부한 개념' in sh, sh[:300]; await o.click('#sheetClose')
        await o.click('[data-adm="stats"]'); await o.wait_for_timeout(900); st = await txt(o, '#v-admin'); assert '1명' in st and '7일 내 학습' in st; await shot(o, 's06_owner_stats')
        await o.click('.tab[data-v="me"]'); await o.wait_for_timeout(300); await o.click('#logout'); await o.wait_for_timeout(500); assert await o.evaluate('SESSION') is None
        for c in (octx, sctx, s2ctx, pctx, gctx): await c.close()
        await b.close()
        print('SERVER E2E OK · 콘솔 오류', errs); assert not errs
asyncio.run(main())
