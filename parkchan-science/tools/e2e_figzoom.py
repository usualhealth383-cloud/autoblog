#!/usr/bin/env python3
"""그림을 폰에서 읽히게 E2E(2026-10-07 콘텐츠 감사 보완안 6).

· 개념 상세 그림은 카드 좌우 여백 없이(390 폭에서 그림 350 px 이상 — 예전 약 300)
· 그림 크게 보기(openFigure)는 처음부터 가로 1.8배(글자가 이미 11 px 넘는 그림만 그대로) · 왼쪽부터 · 무대 밖으로 끌려 나가지 않음
· 끌기(포인터)·휠·＋/−·두 번 누르기 그대로 · 닫으면 누른 자리로 초점
· '그림 읽는 법' 번호 → 크게 보기가 그 줄이 가리키는 자리를 가운데에(그림 속 글자에서 찾음) · 고리 표시 · 아래에 그 줄과 번호들(번호를 바꾸면 자리도)
· 그림 데이터를 받기 전에 번호를 누르면 받은 뒤 열림 · 밝은/어두운 스크린샷

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_figzoom.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_figzoom'; os.makedirs(SC, exist_ok=True)

# 그림 속 글자가 지금 무대(보이는 곳) 안에 있는지 · 무대 가운데에서 얼마나 떨어졌는지
NEAR = """(txt => { const st = document.getElementById('fvStage').getBoundingClientRect();
  const t = [...document.querySelectorAll('#fvStage text')].find(x => x.textContent.replace(/\\s+/g, '').includes(txt));
  if (!t) return null; const r = t.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  return { inside: cx > st.left && cx < st.right && cy > st.top && cy < st.bottom, dx: Math.abs(cx - (st.left + st.width / 2)), dy: Math.abs(cy - (st.top + st.height / 2)), w: st.width }; })"""
TF = "(() => { const m = (document.querySelector('#fvStage svg').style.transform || '').match(/translate\\(([-\\d.]+)px, ?([-\\d.]+)px\\) scale\\(([\\d.]+)\\)/); return m ? m.slice(1).map(Number) : null; })()"
EDGE = """(() => { const st = document.getElementById('fvStage').getBoundingClientRect(), r = document.querySelector('#fvStage svg').getBoundingClientRect();
  return { l: r.left - st.left, r: st.right - r.right, t: r.top - st.top, b: st.bottom - r.bottom, w: r.width, h: r.height, sw: st.width, sh: st.height }; })()"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []

        async def page(color='light'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color, service_workers='block')
            await ctx.add_init_script(NO_INTRO)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await auto_yes(pg)
            await pg.goto(APP); await pg.wait_for_timeout(600)
            await pg.click('#goLogin'); await pg.click('[data-demo^="student"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
            return pg

        async def detail(pg, cid):
            await pg.evaluate(f"detailIdx = CONCEPTS.findIndex(c => c.id === '{cid}'); show('detail')"); await pg.wait_for_timeout(350)

        # ───────── 1) 그림 데이터를 받기 전 — 번호를 누르면 받은 뒤 열린다 ─────────
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); await ctx.add_init_script(NO_INTRO)
        z = await ctx.new_page(); z.on('pageerror', lambda e: errs.append(str(e)))
        gate = asyncio.Event()
        async def hold(route):
            await gate.wait(); await route.continue_()
        await z.route('**/more-*.json', hold)
        await z.goto(APP); await z.wait_for_timeout(600); await z.click('#goGuest'); await z.wait_for_timeout(300)
        await z.evaluate("(() => { const i = CONCEPTS.findIndex((c, i) => isOpen(i) && c.figure && c.howto.length); detailIdx = i >= 0 ? i : CONCEPTS.findIndex(c => c.id === '2203-02'); S.auth = S.auth || null; show('detail'); })()"); await z.wait_for_timeout(300)
        if not await z.evaluate("isOpen(detailIdx)"):   # 손님 무료 범위에 읽는 법 그림이 없으면 전 범위로
            await z.evaluate("S.auth = { code:'MON123', cls:'월목반' }; show('detail')"); await z.wait_for_timeout(300)
        assert await z.evaluate("MORE.ok") is False and await z.locator('#v-detail [data-hz]').count() >= 3
        await z.locator('#v-detail [data-hz]').nth(1).click(); await z.wait_for_timeout(200)
        assert await z.locator('#fv').count() == 0, '받기 전인데 빈 그림이 열림'
        gate.set(); await z.wait_for_function('MORE.ok', timeout=15000); await z.wait_for_timeout(700)
        assert await z.locator('#fv').count() == 1 and (await z.get_attribute('#fv', 'data-at') or '').startswith('1:'), '받은 뒤 크게 보기가 그 자리로 열리지 않음'
        await ctx.close()
        s = await page()
        await s.evaluate("loadMore()"); await s.wait_for_function('MORE.ok', timeout=15000)

        # ───────── 2) 개념 상세 그림 — 카드 좌우 여백 없이 ─────────
        await detail(s, '2203-02')
        w = await s.evaluate("document.querySelector('#v-detail .dcard figure svg').getBoundingClientRect().width")
        assert w >= 350, f'그림 폭 {w}'
        sw = await s.evaluate("document.scrollingElement.scrollWidth"); assert sw <= 390, sw
        assert '번호를 누르면' in await s.inner_text('#v-detail .howto .k')
        await s.evaluate("document.querySelector('#v-detail .dcard figure').scrollIntoView({ block:'start' })"); await s.wait_for_timeout(150)
        await s.screenshot(path=f'{SC}/f01_detail_light.png')

        # ───────── 3) 그림 크게 보기 — 1.8배 · 왼쪽부터 · 무대 안 ─────────
        await s.click('#v-detail figure.zoomable'); await s.wait_for_timeout(400)
        assert await s.get_attribute('#fv', 'data-sc') == '1.75' or float(await s.get_attribute('#fv', 'data-sc')) >= 1.7, await s.get_attribute('#fv', 'data-sc')
        e = await s.evaluate(EDGE)
        assert abs(e['l']) < 1.5 and e['w'] > e['sw'] * 1.6, ('왼쪽부터 · 가로 1.8배가 아님', e)
        assert abs(e['t'] - e['b']) < 2, ('세로 가운데가 아님', e)
        await s.screenshot(path=f'{SC}/f02_fv_open_light.png')
        # 끌기(포인터) — 오른쪽 끝까지 끌어도 무대 밖으로 나가지 않음
        st = await s.locator('#fvStage').bounding_box(); cx, cy = st['x'] + st['width'] / 2, st['y'] + st['height'] / 2
        await s.mouse.move(cx, cy); await s.mouse.down(); await s.mouse.move(cx - 150, cy, steps=6); await s.mouse.up(); await s.wait_for_timeout(100)
        e2 = await s.evaluate(EDGE); assert e2['l'] < -100, ('끌어도 움직이지 않음', e2)
        await s.mouse.move(cx, cy); await s.mouse.down(); await s.mouse.move(cx - 2000, cy - 900, steps=8); await s.mouse.up(); await s.wait_for_timeout(100)
        e3 = await s.evaluate(EDGE); assert abs(e3['r']) < 1.5, ('오른쪽 끝을 넘어 끌려 나감', e3)
        # 휠로 옮기기 · ＋ / − · 두 번 누르기
        await s.mouse.move(cx, cy); await s.mouse.wheel(-300, 0); await s.wait_for_timeout(100)
        e4 = await s.evaluate(EDGE); assert e4['r'] < -100, ('휠로 옮겨지지 않음', e4)
        t0 = await s.evaluate(TF); await s.click('#fvPlus'); await s.wait_for_timeout(80); t1 = await s.evaluate(TF); assert t1[2] > t0[2] * 1.3, (t0, t1)
        await s.click('#fvMinus'); await s.click('#fvMinus'); await s.click('#fvMinus'); await s.wait_for_timeout(80); t2 = await s.evaluate(TF); assert t2[2] == 1, t2
        e5 = await s.evaluate(EDGE); assert abs(e5['l'] - e5['r']) < 2 and abs(e5['t'] - e5['b']) < 2, ('1배인데 가운데가 아님', e5)
        await s.dblclick('#fvStage'); await s.wait_for_timeout(80); assert (await s.evaluate(TF))[2] > 2, '두 번 눌러 키워지지 않음'
        await s.keyboard.press('Escape'); await s.wait_for_timeout(150)
        assert await s.locator('#fv').count() == 0 and await s.evaluate("document.activeElement.matches('figure.zoomable')"), '닫은 뒤 초점이 그림으로 돌아오지 않음'

        # ───────── 4) '그림 읽는 법' 번호 → 그 자리로 ─────────
        await s.locator('#v-detail [data-hz]').nth(2).click(); await s.wait_for_timeout(500)
        assert (await s.get_attribute('#fv', 'data-at') or '').startswith('2:'), '읽는 법 3번 자리를 찾지 못함'
        n = await s.evaluate(f"{NEAR}('톱니모양')")
        assert n and n['inside'] and n['dx'] < n['w'] * 0.3, ('3번(톱니)이 화면 가운데 근처가 아님', n)
        assert await s.locator('#fvStage .fvmark').count() == 1, '자리 표시(고리)가 없음'
        cap = await s.inner_text('#fvCap'); assert '잔물결' in cap and await s.locator('#fvCap [data-fvhz]').count() == 4, cap
        assert await s.get_attribute('#fvCap [data-fvhz="2"]', 'aria-pressed') == 'true'
        await s.screenshot(path=f'{SC}/f03_hz3_light.png')
        # 번호 바꾸기 — 2번(가로축 '연도')
        before = await s.evaluate(TF)
        await s.click('#fvCap [data-fvhz="1"]'); await s.wait_for_timeout(300)
        assert (await s.get_attribute('#fv', 'data-at') or '').startswith('1:') and '가로축' in await s.inner_text('#fvT')
        n2 = await s.evaluate(f"{NEAR}('연도')"); assert n2 and n2['inside'], ('2번(연도)이 보이지 않음', n2)
        assert await s.evaluate(TF) != before, '번호를 바꿔도 자리가 그대로'
        await s.click('#fvClose'); await s.wait_for_timeout(150)
        assert await s.evaluate("document.activeElement.dataset.hz") == '2', '닫은 뒤 초점이 누른 번호로 돌아오지 않음'
        # 다른 그림 — 오른쪽 상자(효소)
        await detail(s, '1305-03'); await s.locator('#v-detail [data-hz]').nth(2).click(); await s.wait_for_timeout(500)
        n3 = await s.evaluate(f"{NEAR}('효소')"); assert n3 and n3['inside'], n3
        await s.click('#fvClose'); await s.wait_for_timeout(150)
        # 읽는 법이 있는 그림 22장 — 번호마다 열리고, 대부분 자리를 찾는다
        tot = await s.evaluate("""(async () => { let n = 0, hit = 0; for (const c of CONCEPTS.filter(c => c.figure && c.howto.length)){ for (let i = 0; i < c.howto.length; i++){
            openFigure(figOf(c.id), c.figure.caption, { list:c.howto, i }); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
            n++; if (document.getElementById('fv').dataset.at) hit++; closeFigure(); } } return [n, hit]; })()""")
        assert tot[0] >= 70 and tot[1] / tot[0] >= 0.85, ('읽는 법 자리를 찾은 비율이 낮음', tot)
        print('읽는 법 자리 찾음', tot)
        await s.context.close()

        # ───────── 5) 어두운 화면 ─────────
        d = await page('dark')
        await d.evaluate("loadMore()"); await d.wait_for_function('MORE.ok', timeout=15000)
        await detail(d, '2203-02'); await d.evaluate("document.querySelector('#v-detail .dcard figure').scrollIntoView({ block:'start' })"); await d.wait_for_timeout(150)
        await d.screenshot(path=f'{SC}/f11_detail_dark.png')
        await d.locator('#v-detail [data-hz]').nth(2).click(); await d.wait_for_timeout(500); await d.screenshot(path=f'{SC}/f12_hz3_dark.png')
        await d.context.close()

        bad = [e for e in errs if 'favicon' not in e]
        assert not bad, bad
        print('FIGZOOM E2E OK · 콘솔 오류', bad)


asyncio.run(main())
