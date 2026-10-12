#!/usr/bin/env python3
"""원장 › 통계 '정답률이 낮은 문항'(벤치마크 #18) — 학생 진도의 문항별 결과를 모아 3명 이상 푼 · 60 % 아래 · 낮은 순 10개, 틀린 곳 알림 수, 눌러서 문항 보기.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_quality.py
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-quality'; os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg); await pg.goto('http://127.0.0.1:8765/index.html?server='); await pg.wait_for_timeout(700)
        await pg.click('#goLogin'); await pg.fill('#lgEmail', 'owner@parkchan.kr'); await pg.fill('#lgPw', '2580'); await pg.click('#lgGo'); await pg.wait_for_timeout(800)
        await pg.wait_for_function('MORE.ok', timeout=20000)
        ids = await pg.evaluate("""async () => { const st = await DBX.students(), codes = st.map(s => s.code).slice(0, 4), qs = BANK.filter(q => !isUM(q) && q.type === 'mc').slice(0, 3).map(q => q.id);
            // A: 4명 중 1명(25 %) · B: 4명 중 2명(50 %) · C: 4명 중 4명(100 %, 안 나와야) · D: 2명만 푼 0 %(3명 미만, 안 나와야)
            const D = BANK.find(q => !isUM(q) && q.type === 'ox').id;
            for (let i = 0; i < codes.length; i++){ const bh = { [qs[0]]: i === 0 ? 'o' : 'x', [qs[1]]: i < 2 ? 'o' : 'x', [qs[2]]: 'o' }; if (i < 2) bh[D] = 'x';
              const prev = await DBX.loadProgress(codes[i]) || {}; await DBX.saveProgress(codes[i], { ...prev, bh }); }
            d0 = JSON.parse(localStorage.getItem('pcs.db.v2')); d0.feedback = d0.feedback || []; d0.feedback.push({ id:1, uid:'a-student', kind:'content', body:'정답이 이상해요', ref:'bank:' + qs[0], at:new Date().toISOString(), done_at:null }); localStorage.setItem('pcs.db.v2', JSON.stringify(d0));
            return { qs, D, n:codes.length }; }""")
        assert ids['n'] == 4, ids
        await pg.reload(); await pg.wait_for_timeout(900); await pg.wait_for_function('MORE.ok', timeout=20000)
        await pg.click('[data-adm="stats"]'); await pg.wait_for_timeout(900)
        rows = await pg.locator('.qual .qrow').all_inner_texts()
        got = await pg.evaluate("[...document.querySelectorAll('.qual .qrow')].map(b => b.dataset.qprev)")
        assert got[:2] == ids['qs'][:2] and ids['qs'][2] not in got and ids['D'] not in got, (got, ids)
        assert '25' in rows[0] and '4명 중 1명 맞힘' in rows[0] and '틀린 곳 알림 1건' in rows[0], rows[0]
        assert '50' in rows[1] and '알림' not in rows[1], rows[1]
        clip = await pg.evaluate("[...document.querySelectorAll('.qual .qrow .qb')].filter(e => e.scrollWidth > e.clientWidth + 1).length"); assert clip == 0
        await pg.locator('.qual').screenshot(path=f'{SC}/q1_list.png')
        await pg.click(f'[data-qprev="{ids["qs"][0]}"]'); await pg.wait_for_timeout(400)
        sh = await pg.inner_text('.sheet'); assert '정답' in sh and ids['qs'][0] in sh, sh[:300]
        assert await pg.locator('.sheet .qpch li.ok').count() == 1
        await pg.screenshot(path=f'{SC}/q2_preview.png')
        assert not errs, errs
        print('QUALITY OK', len(rows)); await b.close()
asyncio.run(main())
