#!/usr/bin/env python3
"""로컬 모드 E2E(v2) — 계정·학생·보호자·원장·이용권·통계 흐름을 브라우저에서 끝까지 돌려 본다.

전제: docs/parkchan 이 http://127.0.0.1:8765 에 떠 있다.   사용: python3 tools/e2e_local.py [스크린샷 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
APP = 'http://127.0.0.1:8765/index.html'
SC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/e2e_local'; os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        async def page():
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}, device_scale_factor=2)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
            await pg.goto(APP); await pg.wait_for_timeout(500)
            return ctx, pg
        shot = lambda pg, n: pg.screenshot(path=f'{SC}/{n}.png', full_page=True)
        async def txt(pg, sel): return await pg.locator(sel).first.inner_text()

        # ── 게스트: 둘러보기 → 오늘 → 잠긴 개념 ──
        ctx, s = await page()
        assert await s.evaluate('view') == 'auth'; await shot(s, 'l01_start')
        await s.click('#goGuest'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'today'
        assert '체험' in await txt(s, '.pill'); await shot(s, 'l02_guest_today')
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
        assert await s.locator('.row.locked').count() > 100, '게스트에게 잠긴 개념이 없음'
        await s.click('.row.locked'); await s.wait_for_timeout(200); assert await s.locator('#sheetBg').count() == 1; await s.click('#sheetClose')
        # 검색 · 필터
        await s.fill('#listQ', '효소'); await s.wait_for_timeout(300)
        n = await s.locator('.row').count(); assert 1 <= n <= 20, f'검색 결과 {n}'; await shot(s, 'l03_search')
        await s.fill('#listQ', ''); await s.wait_for_timeout(200)

        # ── 학생 회원가입(학원 코드 포함) ──
        await s.click('.tab[data-v="me"]'); await s.click('#goAuth'); await s.wait_for_timeout(200); await s.click('#goSignup'); await s.wait_for_timeout(200)
        await s.click('#suGo'); assert '이름' in await txt(s, '.err')
        await s.fill('#suName', '테스트학생'); await s.fill('#suEmail', 'bad'); await s.fill('#suPw', '123456'); await s.click('#suGo'); assert '이메일' in await txt(s, '.err')
        await s.fill('#suEmail', 'stu1@test.kr'); await s.fill('#suCode', 'MON123'); await s.click('#suGo'); assert '약관' in await txt(s, '.err')
        await s.click('[data-legal="terms"]'); await s.wait_for_timeout(200); assert '이용약관' in await txt(s, '.sheet h3'); await s.click('#sheetClose')
        await s.check('#suAgree'); await shot(s, 'l04_signup'); await s.click('#suGo'); await s.wait_for_timeout(700)
        assert await s.evaluate('view') == 'today' and await s.evaluate('S.auth && S.auth.cls') == '월목반', '학생 가입+코드 연결 실패'
        assert '테스트학생' in await txt(s, '.hello'); await shot(s, 'l05_student_today')
        # 출석 (로컬 코드) · 문제 · 북마크 · 공유
        att = await s.evaluate('attCode(attWindow())')
        await s.click('#attOpen'); await s.fill('#attIn', att); await s.click('#attGo'); await s.wait_for_timeout(400); assert '출석' in await txt(s, '.pill')
        await s.click('[data-bm]'); await s.wait_for_timeout(100); assert await s.evaluate('S.bm.length') == 1
        await s.click('#goQuiz'); await s.wait_for_timeout(300); ans = await s.evaluate('qState.q.answer'); await s.click(f'.opt[data-p="{1 if ans != 1 else 2}"]'); await s.wait_for_timeout(300)
        assert await s.evaluate('S.done.length') == 1 and await s.evaluate('S.wrong.length') == 1 and await s.evaluate('S.stats.a') == 1
        await shot(s, 'l06_quiz_wrong'); await s.click('#grade'); await s.wait_for_timeout(200)
        # 통계 · 복습
        await s.click('.tab[data-v="stats"]'); await s.wait_for_timeout(400); assert '연속 학습' in await txt(s, '.tiles'); assert await s.locator('.cal .c.on').count() == 1; await shot(s, 'l07_stats')
        await s.click('#goReview'); await s.wait_for_timeout(300); assert await s.evaluate('qState.mode') == 'review'
        ans = await s.evaluate('qState.q.answer'); await s.click(f'.opt[data-p="{ans}"]'); await s.wait_for_timeout(200); assert await s.evaluate('S.stats.c') == 1
        await s.click('#grade'); await s.wait_for_timeout(200); assert await s.evaluate('view') == 'quiz'
        # 오답 노트 · 지금 다시 풀기
        await s.click('.tab[data-v="wrong"]'); await s.wait_for_timeout(300); assert await s.locator('[data-retry]').count() == 1; await shot(s, 'l08_wrong')
        await s.click('[data-retry]'); await s.wait_for_timeout(200); ans = await s.evaluate('qState.q.answer'); await s.click(f'.opt[data-p="{ans}"]'); await s.wait_for_timeout(200)
        assert await s.evaluate('S.wrong[0].cleared') is True
        # 교재 필터: 북마크 1 · 공부함 ≥1
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(200); await s.click('[data-lf="북마크"]'); await s.wait_for_timeout(200); assert await s.locator('.row').count() == 1
        await s.click('[data-lf="전체"]'); await s.wait_for_timeout(200); assert await s.locator('.row.locked').count() == 0, '수강생인데 잠긴 개념'
        # 내 정보 · 프로필 수정 · 로그아웃
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); assert '학원 수강생' in await txt(s, '.badge'); await shot(s, 'l09_me')
        await s.click('#editProfile'); await s.fill('#epPhone', '01011112222'); await s.click('#epSave'); await s.wait_for_timeout(200); assert await s.evaluate('ACC.phone') == '01011112222'
        await s.click('#logout'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'auth' and await s.evaluate('ACC') is None
        # 다시 로그인 → 진도 유지
        await s.click('#goLogin'); await s.fill('#lgEmail', 'stu1@test.kr'); await s.fill('#lgPw', 'wrongpw'); await s.click('#lgGo'); await s.wait_for_timeout(200); assert '다릅니다' in await txt(s, '.err')
        await s.fill('#lgPw', '123456'); await s.click('#lgGo'); await s.wait_for_timeout(500); assert await s.evaluate('S.done.length') == 1 and await s.evaluate('S.auth.code') == 'MON123'
        await ctx.close()

        # ── 보호자: 가입 → 자녀 연결 → 자녀 화면 ──
        ctx, pr = await page()
        await pr.click('#goSignup'); await pr.click('[data-role="parent"]'); await pr.fill('#suName', '테스트보호자'); await pr.fill('#suEmail', 'par1@test.kr'); await pr.fill('#suPw', '123456'); await pr.check('#suAgree'); await pr.click('#suGo'); await pr.wait_for_timeout(500)
        assert await pr.evaluate('view') == 'parent' and await pr.locator('#childIn').count() == 1
        await pr.fill('#childIn', 'ZZZ000'); await pr.click('#childGo'); await pr.wait_for_timeout(200); assert '찾을 수 없' in await txt(pr, '.err')
        await pr.fill('#childIn', 'MON123'); await pr.click('#childGo'); await pr.wait_for_timeout(500)
        body = await txt(pr, '#v-parent'); assert '박○○ 학생' in body and '출석' in body, body[:200]; await shot(pr, 'l10_parent')
        assert [t for t in await pr.locator('.tab').all_inner_texts()] == ['자녀', '교재', '내 정보']
        await ctx.close()

        # ── 원장: 로그인 → 학생 상세 → 통계 → 설정(반·이용권) ──
        ctx, o = await page()
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', '2580'); await o.click('#lgGo'); await o.wait_for_timeout(600)
        assert await o.evaluate('view') == 'admin'; await shot(o, 'l11_admin_students')
        await o.click('[data-stu="MON123"]'); await o.wait_for_timeout(400); sh = await txt(o, '.sheet'); assert '박○○ 학생' in sh and '보호자 연결 1명' in sh and '이달 출석' in sh, sh[:300]; await shot(o, 'l12_student_sheet'); await o.click('#sheetClose')
        await o.click('[data-adm="stats"]'); await o.wait_for_timeout(500); st = await txt(o, '#v-admin'); assert '수강생' in st and '반별 출석' in st; await shot(o, 'l13_admin_stats')
        await o.click('[data-adm="settings"]'); await o.wait_for_timeout(400)
        await o.fill('#clsName', '일요반'); await o.fill('#clsStart', '10:00'); await o.click('#clsAdd'); await o.wait_for_timeout(400); assert '일요반' in await txt(o, '#v-admin')
        await o.select_option('#passDays', '90'); await o.click('#passIssue'); await o.wait_for_timeout(400); pcode = await o.evaluate('issuedPass.code'); assert len(pcode) == 6; await shot(o, 'l14_admin_settings')
        await o.click('[data-adm="notice"]'); await o.click('[data-chip="시험 안내"]'); await o.select_option('#ntCls', '전체'); await o.click('#ntSend'); await o.wait_for_timeout(300); assert '읽음 0' in await txt(o, '.sent .r')
        await ctx.close()

        # ── 학원 밖 학생: 가입(코드 없음) → 잠김 → 이용권 코드 등록 → 전 범위 ──
        # (로컬 모드는 브라우저 저장소가 곧 서버라, 같은 컨텍스트에서 원장이 먼저 코드를 만든다)
        ctx, g = await page()
        await g.click('#goLogin'); await g.fill('#lgEmail', 'owner@parkchan.kr'); await g.fill('#lgPw', '2580'); await g.click('#lgGo'); await g.wait_for_timeout(500)
        await g.click('[data-adm="settings"]'); await g.wait_for_timeout(300); await g.select_option('#passDays', '90'); await g.click('#passIssue'); await g.wait_for_timeout(300); pcode = await g.evaluate('issuedPass.code')
        await g.click('.tab[data-v="me"]'); await g.wait_for_timeout(200); await g.click('#logout'); await g.wait_for_timeout(300)
        await g.click('#goSignup'); await g.fill('#suName', '외부학생'); await g.fill('#suEmail', 'out1@test.kr'); await g.fill('#suPw', '123456'); await g.check('#suAgree'); await g.click('#suGo'); await g.wait_for_timeout(500)
        assert await g.evaluate('fullAccess()') is False
        await g.click('.tab[data-v="me"]'); await g.wait_for_timeout(200); await g.click('#goPlans'); await g.wait_for_timeout(300); await shot(g, 'l15_plans')
        await g.fill('#passIn', 'NOPE00'); await g.click('#passGo'); await g.wait_for_timeout(200); assert '없는' in await txt(g, '.err')
        await g.fill('#passIn', pcode); await g.click('#passGo'); await g.wait_for_timeout(400); assert await g.evaluate('fullAccess()') is True, '이용권 등록 후에도 잠김'
        await g.fill('#passIn', pcode); await g.click('#passGo'); await g.wait_for_timeout(200); assert '이미' in await txt(g, '.err')
        await g.click('.tab[data-v="list"]'); await g.wait_for_timeout(300); assert await g.locator('.row.locked').count() == 0
        # 계정 삭제
        await g.click('.tab[data-v="me"]'); await g.wait_for_timeout(200); await g.click('#delAccount'); await g.wait_for_timeout(400); assert await g.evaluate('view') == 'auth'
        await g.click('#goLogin'); await g.fill('#lgEmail', 'out1@test.kr'); await g.fill('#lgPw', '123456'); await g.click('#lgGo'); await g.wait_for_timeout(200); assert '다릅니다' in await txt(g, '.err'), '삭제된 계정으로 로그인됨'
        await ctx.close(); await b.close()
        print('LOCAL E2E OK · 콘솔 오류', errs); assert not errs
asyncio.run(main())
