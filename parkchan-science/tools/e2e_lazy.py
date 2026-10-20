#!/usr/bin/env python3
"""첫 로딩 E2E — 문제 은행·자료 탐구·그림(more-지문.json)을 앱 파일에서 떼어 첫 화면 뒤에 받는다(2026-10-02).

· 앱 파일이 가볍다(1.7MB 아래) · 데이터 파일 이름이 서비스 워커 미리 받기 목록과 같다
· 데이터가 늦게 와도: 첫 화면이 바로 그려지고, 문항 수는 맞게 보이고, 그림 자리는 같은 비율로 비어 있다가 채워진다
· 문제 은행 탭은 자리 표시 → 받으면 그려짐 · 개념 상세의 확인 문제(그 개념 OX)도 자리 표시 → 받으면 채워짐 · '이 소단원 문제 풀기'를 먼저 누르면 받은 뒤 바로 문제로
· 받기가 실패하면 '다시 받기' 안내 → 누르면 받아진다
· (2026-10-14 앱 파일 덜기) 오늘의 한 마디는 받기 전에 그려지고(글귀·사람·분야), 원문·출처는 접기 안 자리 표시 → 받으면 그 자리에 채워진다.
  개념 상세의 오해 풀이(진실·까닭)·용어 뜻·용어 말풍선도 같다 — 받기 전엔 문장·이름만, 받으면 제자리에.
  앱 파일 한도 1,600,000 B(덜어 낸 뒤 1,476,992 B + 여유 약 120 KB — 여유가 진짜로 남게 지킨다)
전제: docs/parkchan 이 :8765.   사용: python3 tools/e2e_lazy.py [--shots 폴더]
"""
import asyncio, sys, os, re, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = __import__('os').environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_lazy'; os.makedirs(SC, exist_ok=True)
PAGES = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'parkchan'


async def main():
    idx = (PAGES / 'index.html').stat().st_size
    more = [p for p in PAGES.glob('more-*.json')]
    assert len(more) == 1, more
    assert idx < 1_600_000, f'앱 파일이 다시 무거워졌다: {idx:,} B(한도 1,600,000 B — 첫 화면에 안 쓰는 데이터는 more-*.json 으로)'
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
        assert await s.locator('#v-today .path .ps').count() == 3 and await s.locator('#v-today .ps.now #pRead').count() == 1, '데이터를 기다리느라 오늘 화면이 안 그려짐'   # 손님은 빈 복습 단계 없이 3단계(docs/23 S18)
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
        # ③ 한 마디 원문·출처 · 오해 풀이 · 용어 뜻 — 받기 전에 첫 화면(한 마디 포함)이 그려지고, 받으면 그 자리에 채워진다
        ctx3 = await b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); await ctx3.add_init_script(NO_INTRO)
        s3 = await ctx3.new_page(); await auto_yes(s3)
        s3.on('pageerror', lambda e: errs.append(str(e)))
        gate3 = asyncio.Event()
        async def hold3(route):
            await gate3.wait(); await route.continue_()
        await s3.route('**/more-*.json', hold3)
        await s3.goto(APP); await s3.wait_for_timeout(700)
        await s3.click('#goGuest'); await s3.wait_for_timeout(500)
        assert await s3.evaluate('MORE.ok') is False
        q = await s3.evaluate('(() => { const q = quoteToday(); return { id:q.id, ko:q.ko, who:q.who, kn:q.kindName, src:q.src || null, orig:q.orig || null }; })()')
        assert q['src'] is None and q['orig'] is None, '원문·출처가 앱 파일에 남아 있음(나중에 받는 데이터로 옮겼다)'
        assert await s3.inner_text('#v-today .qsay blockquote') == f"“{q['ko']}”" and q['who'] in await s3.inner_text('#v-today .qsay .by'), '받기 전에 한 마디가 안 그려짐'
        assert q['kn'] and q['kn'] in await s3.inner_text('#v-today .qsay .k'), '받기 전에 한 마디 분야가 안 보임'
        await s3.click('#v-today .qsay .qmore summary'); await s3.wait_for_timeout(200)
        assert await s3.locator(f'#v-today .qsay [data-lz="q:{q["id"]}"] .lzi').count() == 2 and '받는 중' in await s3.inner_text('#v-today .qsay .qmore'), '원문·출처 자리 표시가 없음'
        assert await s3.locator('#v-today .qsay .qmore .note').count() == 1, '한 줄 풀이(note)는 받기 전에도 보여야 함'
        await s3.locator('#v-today .qsay').scroll_into_view_if_needed(); await s3.screenshot(path=f'{SC}/l05_quote_waiting.png')
        # 개념 상세 — 본문을 펼쳐 둔 개념(용어·오해 있음): 오해 문장·용어 이름은 보이고 진실·뜻은 자리 표시, 용어 말풍선은 '받는 중'
        ci = await s3.evaluate("CONCEPTS.findIndex((c, i) => isOpen(i) && c.myths.length && c.terms.length)")
        await s3.evaluate(f"dOpenSet(CONCEPTS[{ci}].id, true); detailIdx = {ci}; show('detail')"); await s3.wait_for_timeout(300)
        cid = await s3.evaluate(f'CONCEPTS[{ci}].id')
        assert await s3.locator(f'#v-detail [data-lz="my:{cid}"] .myth').count() == await s3.evaluate(f'CONCEPTS[{ci}].myths.length'), '오해 자리 표시가 없음'
        assert await s3.locator(f'#v-detail [data-lz="tm:{cid}"] dd .lzi').count() == await s3.evaluate(f'CONCEPTS[{ci}].terms.length'), '용어 뜻 자리 표시가 없음'
        assert await s3.evaluate(f"plain(CONCEPTS[{ci}].myths[0].x)") in await s3.inner_text('#v-detail .dmyth'), '받기 전에 오해 문장이 안 보임'
        tt = s3.locator('#v-detail .tterm').first; has_tt = await tt.count() == 1
        if has_tt:
            await tt.click(); await s3.wait_for_timeout(150); assert '받는 중' in await s3.inner_text('#ttip'), '용어 말풍선 자리 표시가 없음'
        await s3.screenshot(path=f'{SC}/l06_detail_terms_waiting.png', full_page=True)
        gate3.set(); await s3.wait_for_function('MORE.ok', timeout=8000); await s3.wait_for_timeout(400)
        assert await s3.locator('[data-lz]').count() == 0, '받은 뒤에도 자리 표시가 남음'
        my = await s3.evaluate(f"CONCEPTS[{ci}].myths.map(m => [plain(m.o), plain(m.why || '')])")
        mt = await s3.inner_text('#v-detail .dmyth')
        assert all(o and o in mt and w in mt for o, w in my), '받은 뒤 오해 풀이(진실·까닭)가 제자리에 안 채워짐'
        tv = await s3.evaluate(f"CONCEPTS[{ci}].terms.map(t => t.v)")
        assert all(tv) and [x.strip() for x in await s3.locator('#v-detail dl.terms dd').all_inner_texts()] == [v.strip() for v in tv], '받은 뒤 용어 뜻이 제자리에 안 채워짐'
        if has_tt:
            tip = await s3.inner_text('#ttip'); assert '받는 중' not in tip and len(tip) > 8, f'받은 뒤 말풍선에 뜻이 안 채워짐: {tip}'
        # 한 마디: 다시 그리지 않아도(오늘 화면은 숨은 채) 접기 안에 원문·출처가 채워져 있다
        q2 = await s3.evaluate(f"(() => {{ const q = QUOTES.find(x => x.id === '{q['id']}'); return {{ src:q.src, orig:q.orig || '' }}; }})()")
        assert q2['src'] and await s3.inner_text('#v-today .qsay .qmore .src') == f"출처 · {q2['src']}", '받은 뒤 한 마디 출처가 안 채워짐'
        assert not q2['orig'] or q2['orig'] in await s3.inner_text('#v-today .qsay .qmore .orig'), '받은 뒤 한 마디 원문이 안 채워짐'
        assert await s3.evaluate("QUOTES.every(q => q.src && q.url && q.kindName)"), '받은 뒤 출처·주소·분야가 빈 글귀'
        await s3.evaluate("show('today')"); await s3.wait_for_timeout(300)
        await s3.click('#v-today .qsay .qmore summary'); await s3.wait_for_timeout(200)
        await s3.locator('#v-today .qsay').scroll_into_view_if_needed(); await s3.screenshot(path=f'{SC}/l07_quote_loaded.png')
        assert not errs, errs
        print('LAZY E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
