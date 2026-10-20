#!/usr/bin/env python3
"""합답형 하나씩 판정(벤치마크 #10) — ㄱㄴㄷ를 옳아요/틀려요로 판정 → 조합이 선지로 정해짐 → 채점,
선지에 없는 조합은 채점 안 함, 해설에 '내 판정'과 갈린 곳, 방식 기억, 시험처럼에는 없음.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_multistep.py
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = '/tmp/pcs-e2e-multistep'; os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg); await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(800)
        await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        await pg.wait_for_function('MORE.ok', timeout=20000)
        n = await pg.evaluate("BANK.filter(q => !isUM(q) && multiSplit(q)).length"); assert n >= 200, n
        ids = await pg.evaluate("BANK.filter(q => !isUM(q) && multiSplit(q) && multiSplit(q).rows.length === 3).slice(0, 2).map(q => q.id)")
        await pg.evaluate(f"startBank(BANK.filter(q => {ids}.includes(q.id)), '시험')"); await pg.wait_for_timeout(500)
        assert await pg.locator('#sjTog').count() == 1 and await pg.locator('.sjbox').count() == 0, '처음엔 선지에서 고르기'
        await pg.click('#sjTog'); await pg.wait_for_timeout(200)
        assert await pg.locator('.sjrow').count() == 3 and await pg.is_disabled('#sjGo')
        R = await pg.evaluate("multiSplit(bs.items[0]).rows.map(r => [r.k, r.ok])")
        # 버튼 이름에 보기 글자와 문장 첫머리(GPT 검수 #15 — '옳아요'만 여섯 번 들리던 것)
        nm = await pg.evaluate("[...document.querySelectorAll('.sjrow button')].map(b => b.getAttribute('aria-label') || '')")
        assert len(set(nm)) == 6 and all(x[0] in 'ㄱㄴㄷㄹ' and (x.endswith('옳아요') or x.endswith('틀려요')) and len(x) > 8 for x in nm), nm
        # 1) 일부러 첫 보기를 반대로 판정 → 선지에 있으면 채점, 없으면 막힘
        wrong = {k: (not ok if i == 0 else ok) for i, (k, ok) in enumerate(R)}
        for k, v in wrong.items(): await pg.click(f'[data-sj="{k}|{1 if v else 0}"]'); await pg.wait_for_timeout(80)
        summ = await pg.inner_text('.sjsum'); dis = await pg.is_disabled('#sjGo')
        await pg.screenshot(path=f'{SC}/m1_judge.png', full_page=True)
        if dis:
            assert '선지에 없어요' in summ, summ
            for k, ok in R: await pg.click(f'[data-sj="{k}|{1 if ok else 0}"]'); await pg.wait_for_timeout(80)
            assert not await pg.is_disabled('#sjGo'); await pg.click('#sjGo'); await pg.wait_for_timeout(400)
            assert await pg.evaluate("bankCorrect(bs.items[0], bs.pick)"), '옳게 판정했는데 오답'
            assert await pg.locator('.jme.off').count() == 0
        else:
            await pg.click('#sjGo'); await pg.wait_for_timeout(400)
            assert not await pg.evaluate("bankCorrect(bs.items[0], bs.pick)"), '틀린 판정이 정답 처리'
            off = await pg.locator('.jme.off').all_inner_texts(); assert len(off) == 1 and '여기서 갈렸어요' in off[0], off
        assert await pg.locator('.jme').count() == 3, '해설에 보기마다 내 판정'
        await pg.screenshot(path=f'{SC}/m2_expl.png', full_page=True)
        # 2) 다음 문제도 같은 방식(기억) — 새 세션에서도
        await pg.click('#bankNext'); await pg.wait_for_timeout(300); assert await pg.locator('.sjbox').count() == 1
        await pg.evaluate(f"startBank(BANK.filter(q => {ids}.includes(q.id)), '다시')"); await pg.wait_for_timeout(400)
        assert await pg.locator('.sjbox').count() == 1, '고른 방식을 기억하지 않음'
        # 3) 시험처럼(타이머)에는 없음
        await pg.evaluate(f"startBank(BANK.filter(q => {ids}.includes(q.id)), '시험', true)"); await pg.wait_for_timeout(400)
        assert await pg.locator('#sjTog').count() == 0 and await pg.locator('.sjbox').count() == 0
        assert not errs, errs
        print('MULTISTEP OK', n); await b.close()
asyncio.run(main())
