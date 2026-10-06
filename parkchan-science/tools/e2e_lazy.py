#!/usr/bin/env python3
"""첫 로딩 E2E — 문제 은행·자료 탐구·그림(more-지문.json)을 앱 파일에서 떼어 첫 화면 뒤에 받는다(2026-10-02).

· 앱 파일이 가볍다(1.7MB 아래) · 데이터 파일 이름이 서비스 워커 미리 받기 목록과 같다
· 데이터가 늦게 와도: 첫 화면이 바로 그려지고, 문항 수는 맞게 보이고, 그림 자리는 같은 비율로 비어 있다가 채워진다
· 문제 은행 탭은 자리 표시 → 받으면 그려짐 · 개념 상세의 확인 문제(그 개념 OX)도 자리 표시 → 받으면 채워짐 · '이 소단원 문제 풀기'를 먼저 누르면 받은 뒤 바로 문제로
· 받기가 실패하면 '다시 받기' 안내 → 누르면 받아진다
전제: docs/parkchan 이 :8765.   사용: python3 tools/e2e_lazy.py [--shots 폴더]
"""
import asyncio, sys, os, re, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_lazy'; os.makedirs(SC, exist_ok=True)
PAGES = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'parkchan'


async def main():
    idx = (PAGES / 'index.html').stat().st_size
    more = [p for p in PAGES.glob('more-*.json')]
    assert len(more) == 1, more
    assert idx < 1_700_000, f'앱 파일이 다시 무거워졌다: {idx:,} B'
    sw = (PAGES / 'sw.js').read_text(encoding='utf-8')
    assert f"const DATA = './{more[0].name}';" in sw, '서비스 워커가 미리 받는 데이터 파일 이름이 다르다'
    print(f'앱 {idx/1e6:.2f}MB + 나중에 받는 {more[0].name} {more[0].stat().st_size/1e6:.2f}MB')
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); await ctx.add_init_script(NO_INTRO)
        s = await ctx.new_page(); await auto_yes(s)
        s.on('pageerror', lambda e: errs.append(str(e)))
        s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        # ① 데이터가 늦게 오는 망: 붙잡아 두었다가 놓아 준다
        held = []; gate = asyncio.Event()
        async def hold(route):
            held.append(route.request.url); await gate.wait(); await route.continue_()
        await s.route('**/more-*.json', hold)
        await s.goto(APP); await s.wait_for_timeout(700)
        await s.click('#goGuest'); await s.wait_for_timeout(500)
        assert held and await s.evaluate('MORE.ok') is False
        assert await s.locator('#v-today .path .ps').count() == 4 and await s.locator('#v-today .ps.now #pRead').count() == 1, '데이터를 기다리느라 오늘 화면이 안 그려짐'
        # 교재 상세(그림 있는 개념) — 그림 자리는 같은 비율로
        fi = await s.evaluate("CONCEPTS.findIndex((c, i) => c.figure && isOpen(i))")
        await s.evaluate(f"detailIdx = {fi}; show('detail')"); await s.wait_for_timeout(300)
        slot = s.locator('#v-detail .figslot'); assert await slot.count() == 1, '그림 자리 표시가 없음'
        bb = await slot.bounding_box(); w, h = map(float, (await s.evaluate(f"MORE_META.fv[CONCEPTS[{fi}].id]")).split())
        assert abs(bb['width'] / bb['height'] - w / h) < 0.05, (bb, w, h)
        nx = await s.inner_text('#v-detail .nextup'); n_l = await s.evaluate(f"MORE_META.bl[CONCEPTS[{fi}].lessonId]")
        assert f'{n_l}문항' in nx and n_l > 0, nx
        # 확인 문제(그 개념 OX — 문제 은행에서 옴)는 받기 전엔 자리 표시
        assert await s.locator('#v-detail #dqcBox[aria-busy="true"] .skel').count() == 1 and await s.locator('#v-detail [data-dqc]').count() == 0, '확인 문제 자리 표시가 없음'
        await s.screenshot(path=f'{SC}/l01_detail_waiting.png')
        # '이 소단원 문제 풀기'를 먼저 누른다 → 받은 뒤 바로 문제
        await s.click('#v-detail [data-drill]'); await s.wait_for_timeout(300)
        assert await s.evaluate('view') == 'detail'
        gate.set(); await s.wait_for_function('MORE.ok', timeout=5000); await s.wait_for_timeout(500)
        assert await s.evaluate('view') == 'bank' and await s.evaluate('bs && bs.items.length > 0'), '받은 뒤 문제로 가지 않음'
        assert await s.evaluate('BANK.length') == await s.evaluate('BANK_N') and await s.evaluate('LABS.length') == await s.evaluate('LABS_N')
        await s.evaluate(f"bs = null; detailIdx = {fi}; show('detail')"); await s.wait_for_timeout(300)
        assert await s.locator('#v-detail .figslot').count() == 0 and await s.locator('#v-detail figure svg').count() >= 1, '받은 뒤에도 그림이 비어 있음'
        n_q = await s.evaluate('dqcItems(CONCEPTS[detailIdx]).length')
        assert n_q > 0 and await s.locator('#v-detail [data-dqc]').count() == 2 * n_q, '받은 뒤 확인 문제가 비어 있음'
        assert await s.evaluate("[...document.querySelectorAll('#dqcBox .qi')].every(r => { const q = BANK.find(x => x.id === r.dataset.qi), c = CONCEPTS[detailIdx]; return q && q.lessonId === c.lessonId && +q.concept === +c.no && q.type === 'ox'; })"), '확인 문제가 그 개념 문항이 아님'
        await s.screenshot(path=f'{SC}/l02_detail_loaded.png')
        await s.unroute('**/more-*.json')
        # ② 받기 실패(첫 실행부터 오프라인) → 문제 은행 탭에 '다시 받기'
        ctx2 = await b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); await ctx2.add_init_script(NO_INTRO)
        s2 = await ctx2.new_page(); await auto_yes(s2)
        s2.on('pageerror', lambda e: errs.append(str(e)))
        fail = {'on': True}
        async def flaky(route):
            if fail['on']: await route.abort()
            else: await route.continue_()
        await s2.route('**/more-*.json', flaky)
        await s2.goto(APP); await s2.wait_for_timeout(600)
        await s2.click('#goGuest'); await s2.wait_for_timeout(300)
        await s2.click('.tab[data-v="bank"]'); await s2.wait_for_timeout(300)
        assert await s2.locator('#v-bank .skel').count() == 1, '받는 중 자리 표시가 없음'
        await s2.wait_for_selector('#moreRetry', timeout=9000)
        assert '받지 못했습니다' in await s2.inner_text('#v-bank')
        await s2.screenshot(path=f'{SC}/l03_bank_failed.png')
        fail['on'] = False; await s2.click('#moreRetry')
        await s2.wait_for_function('MORE.ok', timeout=5000); await s2.wait_for_timeout(300)
        assert await s2.locator('#bankRec').count() == 1, '다시 받은 뒤 문제 은행이 안 그려짐'
        await s2.screenshot(path=f'{SC}/l04_bank_loaded.png')
        assert not errs, errs
        print('LAZY E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
