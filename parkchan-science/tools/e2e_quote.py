#!/usr/bin/env python3
"""오늘의 한 마디 E2E — 365일 날마다 다른 명언.

· 글귀가 365개 이상이고, 어느 날에서 시작해 1년(365일)을 잘라 봐도 같은 글귀가 두 번 나오지 않는다(윤년 366일 포함)
· 선생님이 쓴 글(박찬 과학)은 없다 · 모든 글귀에 사람·출처·한 줄 풀이가 있다
· 카드에 분야(과학자·고전…)가 보이고, '다른 한 마디'는 그날만 넘기며 다음 날이면 그날의 글귀로 돌아온다
· 가장 긴 글귀도 카드에서 잘리지 않는다(말줄임 없음)

전제: docs/parkchan 이 :8765.   사용: python3 tools/e2e_quote.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_quote'; os.makedirs(SC, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); await ctx.add_init_script(NO_INTRO); s = await ctx.new_page()
        s.on('pageerror', lambda e: errs.append(str(e)))
        await s.goto(APP); await s.wait_for_timeout(500); await s.click('#goGuest'); await s.wait_for_timeout(500)
        n = await s.evaluate('QUOTES.length'); assert n >= 366, f'글귀가 {n}개 — 1년을 채우지 못함'
        assert await s.evaluate("QUOTES.filter(q => q.who === '박찬 과학' || q.kind === 'teacher').length") == 0, '선생님 글이 남아 있음'
        assert await s.evaluate("QUOTES.every(q => q.ko && q.who && q.src && q.note && q.kindName)"), '빈 칸이 있는 글귀'
        assert await s.evaluate("new Set(QUOTES.map(q => q.id)).size") == n, 'id 중복'
        # 여러 시작일에서 366일씩 — 겹침 없음
        rep = await s.evaluate("""() => { const bad = []; for (const start of ['2026-01-01','2026-11-01','2027-02-28','2028-02-29','2031-07-15']) {
            const seen = new Set(); for (let i = 0; i < 366; i++){ const d = addDays(start, i); const n = QUOTES.length; const k = ((dayNo(d) % n) + n) % n;
              if (seen.has(k)) { bad.push(start + ' +' + i); break; } seen.add(k); } } return bad; }""")
        assert rep == [], f'1년 안에 같은 글귀가 다시 나옴: {rep}'
        # 오늘 카드 · 분야 표시
        q0 = await s.evaluate('quoteToday().id'); k = await s.inner_text('.qsay .k')
        assert '오늘의 한 마디 ·' in k and await s.evaluate('quoteToday().kindName') in k, k
        await s.locator('.qsay').scroll_into_view_if_needed(); await s.screenshot(path=f'{SC}/q01_today.png')
        await s.click('#qNext'); await s.wait_for_timeout(300); q1 = await s.evaluate('quoteToday().id'); assert q1 != q0, '다른 한 마디가 안 넘어감'
        # 다음 날이 되면 넘긴 수는 0으로(그날의 글귀)
        await s.evaluate("S.qskipDay = addDays(todayISO(), -1)"); assert await s.evaluate('quoteToday().id') == q0 and await s.evaluate('S.qskip') == 0, '다음 날에 넘긴 수가 남음'
        # 가장 긴 글귀를 카드에 그려 잘림 확인
        await s.evaluate("""() => { const q = QUOTES.slice().sort((a,b) => b.ko.length - a.ko.length)[0]; const c = todayConcept();
            const box = document.querySelector('.qsay').parentElement; const tmp = document.createElement('div'); tmp.id = 'qlong'; tmp.innerHTML = quoteCard(q, c); box.appendChild(tmp); }""")
        over = await s.evaluate("""() => [...document.querySelectorAll('#qlong .qsay *')].filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible' || getComputedStyle(e).textOverflow === 'ellipsis').map(e => e.className)""")
        assert over == [], f'긴 글귀가 잘림: {over}'
        await s.locator('#qlong').scroll_into_view_if_needed(); await s.screenshot(path=f'{SC}/q02_longest.png')
        # 보관하기 → 보관함
        await s.click('#qKeep'); await s.wait_for_timeout(200); assert await s.evaluate('(S.qkeep||[]).length') == 1
        assert not errs, errs
        print(f'QUOTE E2E OK · 글귀 {n}개 · 콘솔 오류', errs); await b.close()

asyncio.run(main())
