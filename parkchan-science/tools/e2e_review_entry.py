#!/usr/bin/env python3
"""검수 입구(review.html) — 예시 기록을 넣고 날짜를 '오늘'로 옮겨 역할별로 연다 · 원래 기록 보관·되돌리기.
시계를 기록 기준일(t0)보다 20일 뒤로 두고 본다(날짜 옮기기가 맞는지).
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_review_entry.py
"""
import asyncio, sys, os, json, datetime as dt, pathlib
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
SC = '/tmp/pcs-e2e-review'; os.makedirs(SC, exist_ok=True)
FX = json.loads((pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'parkchan' / 'review-fixtures.json').read_text(encoding='utf-8'))
T0 = dt.date.fromisoformat(FX['t0']); TODAY = T0 + dt.timedelta(20)
BASE = 'http://127.0.0.1:8765/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        async def open_as(sc, pre=None):
            ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); pg = await ctx.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.clock.set_fixed_time(dt.datetime(TODAY.year, TODAY.month, TODAY.day, 19, tzinfo=ZoneInfo('Asia/Seoul')))
            await pg.goto(BASE + 'review.html'); await pg.wait_for_timeout(400)
            if pre: await pg.evaluate(f"localStorage.setItem('pcs.v2', {json.dumps(pre)})"); await pg.reload(); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'{SC}/r0_entry.png', full_page=True)
            await pg.click(f'[data-sc="{sc}"]'); await pg.wait_for_url('**/index.html', timeout=10000); await pg.wait_for_timeout(1400)
            return ctx, pg, errs
        # 학생
        ctx, pg, errs = await open_as('student')
        assert await pg.evaluate("ACC && ACC.role") == 'student' and await pg.evaluate("view") == 'today'
        days = await pg.evaluate("S.days"); assert days[-1] == (TODAY - dt.timedelta(1)).isoformat() and len(days) == 7, days
        assert await pg.evaluate("todayISO()") == TODAY.isoformat()
        assert await pg.evaluate("(document.querySelector('#v-today .ps.now')||{}).id") == 'ps-read', '오늘은 아직 공부 전'
        assert await pg.locator('.asgcard').count() == 1 and '3/5' in await pg.locator('.asgcard').inner_text()
        assert 'D-9' in await pg.locator('.passnote', has_text='중간고사').inner_text()
        assert await pg.evaluate("S.wrong.filter(w => !w.cleared).length") >= 5
        await pg.screenshot(path=f'{SC}/r1_student.png'); assert not errs, errs; await ctx.close()
        # 보호자
        ctx, pg, errs = await open_as('parent')
        assert await pg.evaluate("ACC.role") == 'parent' and await pg.evaluate("view") == 'parent'
        t = await pg.inner_text('#v-parent'); assert '선생님 한 마디' in t and '꾸준히' in t, t[:500]
        await pg.screenshot(path=f'{SC}/r2_parent.png', full_page=True); assert not errs, errs; await ctx.close()
        # 원장
        ctx, pg, errs = await open_as('owner')
        assert await pg.evaluate("ACC.role") == 'owner' and await pg.evaluate("view") == 'admin'
        await pg.click('[data-adm="asg"]'); await pg.wait_for_timeout(600); assert '제출 0 / ' in await pg.inner_text('#v-admin')
        assert not errs, errs; await ctx.close()
        # 처음 온 사람 — 소개부터
        ctx, pg, errs = await open_as('guest')
        assert await pg.evaluate("!ACC") and await pg.locator('#introNext').count() == 1, '소개 화면이 아님'
        assert not errs, errs; await ctx.close()
        # 원래 기록 보관 → 되돌리기
        ctx, pg, errs = await open_as('student', pre=json.dumps({'introSeen': True, 'mine': 'real'}))
        await pg.goto(BASE + 'review.html'); await pg.wait_for_timeout(400)
        assert await pg.is_visible('#restore'); await pg.click('#restore'); await pg.wait_for_timeout(300)
        assert json.loads(await pg.evaluate("localStorage.getItem('pcs.v2')")).get('mine') == 'real', '원래 기록이 돌아오지 않음'
        assert await pg.evaluate("localStorage.getItem('pcs.review')") is None and not await pg.is_visible('#restore')
        await ctx.close()
        print('REVIEW ENTRY OK', FX['t0'], '→', TODAY); await b.close()
asyncio.run(main())
