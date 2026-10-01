#!/usr/bin/env python3
"""대단원 마무리 · 실전 모의고사 · 시험처럼(문항당 96초) E2E (로컬 어댑터 ?server=).

· 추출기: --out 임시 폴더로 돌려 대단원 6 × 16문항, 모의고사 2 × 25문항(배점 합 50), 핵심 정리 빈칸, 소단원 연결·첨자·그림 확인
· 보통 문제 은행 풀이(bankPool)·오늘의 복습 덤 문항에는 대단원·모의고사 문항이 섞이지 않는다
· 대단원 마무리: 단원 고르기 → 16문항(마무리 12 + 고난도 4) → 결과·다시 볼 소단원 → 틀린 것은 내일 복습 · 핵심 정리 빈칸(첨자 답 10^-10 m)
· 실전 모의고사: 40분 타이머 · 잠시 멈춤(멈춘 동안 시간이 안 흐름) · 제출 전 채점 없음 · 50점 만점 점수 · 처방 · 문항별 해설 · 진도 기록(작게)
  · 40분이 지나면 저절로 제출
· 손님: 두 갈래가 잠겨 있고 누르면 차분한 이용권 안내
· 시험처럼: 96초가 지나면 '넘김'으로 다음 문제, 오답 노트에 담김, 결과에 '시간을 넘긴 문제'
전제: 앱을 (대단원·모의고사가 든 bank.json 으로) 빌드해 docs/parkchan 을 :8765 에 띄운다.
사용: python3 tools/e2e_unitmock.py [--shots 폴더]
"""
import asyncio, sys, os, json, re, subprocess, tempfile, pathlib, datetime as dt
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
from _extract_common import dangling
APP = 'http://127.0.0.1:8765/index.html?server='
ROOT = pathlib.Path(__file__).resolve().parent.parent
SC = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_unitmock'; os.makedirs(SC, exist_ok=True)


def check_extract():
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'extract_bank.py'), '--out', d], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        bank = json.loads((pathlib.Path(d) / 'bank.json').read_text(encoding='utf-8'))
    lessons = {c['lessonId'] for c in json.loads((ROOT / 'data' / 'concepts.json').read_text(encoding='utf-8'))}
    unit = [q for q in bank if q['step'] == 'unit']; mock = [q for q in bank if q['step'] == 'mock']; recap = [q for q in bank if q['step'] == 'recap']
    for b in '12':
        for u in 'I', 'II', 'III':
            its = [q for q in unit if q['book'] == b and q['unit'] == u]
            assert len(its) == 16, (b, u, len(its))
            assert sorted(int(q['id'].split('-q')[1]) for q in its) == list(range(1, 17))
            assert sum(q['type'] == 'essay' for q in its) == 2, (b, u)                       # 11·12 서술형
        ms = [q for q in mock if q['book'] == b]
        assert len(ms) == 25 and abs(sum(q['points'] for q in ms) - 50) < 1e-9, (b, len(ms), sum(q['points'] for q in ms))
        assert all(q['id'] == f'M{b}-q{int(q["id"].split("-q")[1])}' for q in ms)
    assert len(unit) == 96 and len(mock) == 50
    for q in unit + mock:
        assert q['lessons'] and all(l in lessons for l in q['lessons']) and q['lessonId'] == q['lessons'][0], q['id']
        assert q['type'] == 'essay' or q['answer'] in (1, 2, 3, 4, 5), q['id']
        assert q['explain'], q['id']
        if q['figure']: assert not dangling(q['figure']), q['id']
        if q['type'] == 'multi': assert '<보기>' in q['stem'] + q.get('ask', '') or '고른' in q['stem'] + q.get('ask', ''), q['id']
    assert next(q for q in unit if q['id'] == 'U1-1-q3')['lessons'] == ['1103', '1102', '1104']
    assert '<sup>' in json.dumps(unit + mock, ensure_ascii=False) and '<sub>' in json.dumps(unit + mock, ensure_ascii=False)
    assert any(q.get('table') for q in unit) and any(q.get('data') for q in mock) and any(q.get('ask') for q in mock)
    assert len(recap) == 120 and all(q['type'] == 'blank' and q['answer'] and '＿＿＿' in q['stem'] for q in recap)
    assert next(q for q in recap if q['id'] == 'U1-1-b1')['answer'] == '10⁻¹⁰ m'
    print(f'추출 OK · 대단원 {len(unit)} · 모의고사 {len(mock)} (배점 50 × 2) · 핵심 정리 빈칸 {len(recap)}')
    return bank


async def main():
    check_extract()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []

        async def page(color='light'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=color); await ctx.add_init_script(NO_INTRO)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await pg.clock.install(time=dt.datetime(2026, 10, 5, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=9))))
            await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(600)
            return pg

        async def login(pg):
            await pg.click('#goLogin'); await pg.fill('#lgEmail', 'student@demo.kr'); await pg.fill('#lgPw', '1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
            assert await pg.evaluate('fullAccess()')
            await pg.click('.tab[data-v="bank"]'); await pg.wait_for_function('MORE.ok', timeout=15000); await pg.wait_for_timeout(300)

        SMALL = """() => [...document.querySelectorAll('#v-bank button, #v-bank [role=region], #sheet button')].filter(e => e.offsetParent !== null && !e.closest('.chipbar') && !e.classList.contains('flag') && !e.classList.contains('more'))
          .map(e => [e.id || e.className || e.tagName, Math.round(e.getBoundingClientRect().height)]).filter(([, h]) => h < 44)"""

        async def big(pg, where):
            sm = await pg.evaluate(SMALL); assert not sm, f'{where}: 44px 보다 작은 목표 {sm[:5]}'

        async def answer(pg, ok):
            q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { type:q.type, answer:q.answer }; })()")
            if q['type'] == 'ox': await pg.click(f'[data-ox="{q["answer"] if ok else ("X" if q["answer"] == "O" else "O")}"]')
            elif q['type'] in ('mc', 'multi'): a = int(q['answer']); await pg.click(f'[data-bp="{a if ok else (1 if a != 1 else 2)}"]')
            elif q['type'] == 'blank': await pg.fill('#blankIn', str(q['answer']) if ok else '모르겠음'); await pg.click('#blankGo')
            else: await pg.click('#essayShow'); await pg.wait_for_timeout(80); await pg.click(f'[data-ess="{"맞음" if ok else "틀림"}"]')
            await pg.wait_for_timeout(80)

        # ───────── 1) 학생 — 보통 풀이에 섞이지 않는다 · 대단원 마무리 ─────────
        s = await page()
        await login(s)
        assert await s.evaluate("BANK.filter(isUM).length") == 266
        assert await s.evaluate("bankPool().every(q => !isUM(q)) && bankPool().length > 1000"), '보통 풀이에 대단원·모의고사 문항이 섞임'
        await s.evaluate("bankSel = { ...bankSel, lesson:'1103' }"); assert await s.evaluate("bankPool().every(q => !isUM(q))")
        await s.evaluate("bankSel = { book:'전체', unit:'전체', lesson:'전체', type:'전체', n:10, only:'전체' }"); await s.evaluate("renderBank()")
        assert await s.evaluate("MORE_META.bl['1103']") == await s.evaluate("BANK.filter(q => q.lessonId === '1103' && !isUM(q)).length"), '소단원 문항 수에 대단원 문항이 섞임'
        t = await s.inner_text('#v-bank'); assert '대단원 마무리' in t and '실전 모의고사' in t and '시험처럼' in t, t[:300]
        await s.locator('.umsec').scroll_into_view_if_needed(); await s.screenshot(path=f'{SC}/u01_bank_entries.png')
        await s.click('[data-um="unit"]'); await s.wait_for_timeout(250)
        assert await s.locator('[data-ustart]').count() == 6 and await s.locator('[data-urecap]').count() == 6
        await s.screenshot(path=f'{SC}/u02_unit_pick.png'); await big(s, '대단원 고르기')
        await s.click('[data-ustart="1-I"]'); await s.wait_for_timeout(250)
        assert await s.evaluate("bs.kind === 'unit' && bs.items.length === 16 && bs.items.map(q => q.id).join() === Array.from({length:16}, (_, i) => 'U1-1-q' + (i+1)).join()")
        assert '마무리 1' in await s.inner_text('.qhead')
        for i in range(16):
            if i == 4: assert await s.locator('#v-bank .qtab').count() == 1, '5번 표가 안 보임'
            await answer(s, i % 4 != 0)                 # 1·5·9·13번은 틀린다
            if i == 12: assert '고난도 13' in await s.inner_text('.qhead'); await s.screenshot(path=f'{SC}/u03_unit_graded.png', full_page=True)
            if await s.locator('#bankNext').count(): await s.click('#bankNext'); await s.wait_for_timeout(80)
        r = await s.inner_text('#v-bank'); assert '12' in await s.inner_text('.result .big') and '다시 볼 소단원' in r and '대단원 마무리' in r, r[:400]
        assert await s.locator('.rxrow').count() >= 1 and await s.locator('.rxrow [data-drill]').count() >= 1
        assert await s.evaluate("JSON.stringify(S.ux['1-I'].slice(0,2))") == '[12,16]'
        ws = await s.evaluate("S.wrong.filter(w => /^U1-1-/.test(w.b)).map(w => [w.b, w.d, lessonOfW(w)])")
        assert len(ws) == 4 and all(w[1] == '2026-10-06' for w in ws) and ws[0][2] == '1101', ws
        await s.screenshot(path=f'{SC}/u04_unit_result.png', full_page=True)
        await s.click('#bankQuit2'); await s.wait_for_timeout(200); assert await s.evaluate("umPick") == 'unit'
        # 핵심 정리 빈칸 — 위 첨자 답을 자판으로(10^-10 m)
        await s.click('[data-urecap="1-I"]'); await s.wait_for_timeout(200)
        assert await s.evaluate("bs.kind === 'recap' && bs.items.length === 20 && bs.items[0].id === 'U1-1-b1'")
        await s.fill('#blankIn', '10^-10 m'); await s.click('#blankGo'); await s.wait_for_timeout(120)
        assert '맞혔습니다' in await s.inner_text('.verdict')
        await s.click('#bankQuit'); await s.wait_for_timeout(150); await s.click('#umBack'); await s.wait_for_timeout(150)
        # 다음 날 오늘의 복습: 대단원 오답이 기한으로 나오고, 덤 문항(다른 소단원)에는 섞이지 않는다
        await s.clock.fast_forward(24 * 3600 * 1000)
        await s.evaluate("dayRoll(); show('today')"); await s.wait_for_timeout(200)
        plan = await s.evaluate("(() => { const p = reviewPlan(true); return p.items.map(e => [e.w ? wKey(e.w) : '', e.q ? e.q.id : '']); })()")
        assert any(k.startswith('b:U1-1-') for k, _ in plan) and not any(re.match(r'^[UM]\d', q) for _, q in plan if q), plan

        # ───────── 2) 실전 모의고사 — 타이머 · 멈춤 · 제출 · 점수 · 처방 ─────────
        await s.click('.tab[data-v="bank"]'); await s.wait_for_timeout(200)
        await s.click('[data-um="mock"]'); await s.wait_for_timeout(200)
        assert '40분 타이머 켬' in await s.inner_text('#mockTimer')
        await s.screenshot(path=f'{SC}/m01_mock_pick.png'); await big(s, '모의고사 고르기')
        await s.click('[data-mstart="1"]'); await s.wait_for_timeout(250)
        assert await s.evaluate("mx && mx.items.length === 25 && mx.items.reduce((a, q) => a + q.points, 0) === 50")
        assert (await s.inner_text('#mxClock')).startswith(('40:00', '39:5'))
        await s.clock.fast_forward(60_000); await s.wait_for_timeout(150)
        assert (await s.inner_text('#mxClock')).startswith(('39:0', '38:5')), await s.inner_text('#mxClock')
        # 고르기만 하고 채점은 없다
        a1 = await s.evaluate('mx.items[0].answer'); await s.click(f'[data-mxp="{a1 % 5 + 1}"]'); await s.wait_for_timeout(80)
        assert await s.locator('#v-bank .verdict').count() == 0 and await s.locator('#v-bank .opt.ok, #v-bank .opt.bad').count() == 0
        await s.click(f'[data-mxp="{a1}"]'); await s.wait_for_timeout(80); assert await s.evaluate('mx.picks[0]') == a1     # 바꿀 수 있다
        await s.screenshot(path=f'{SC}/m02_mock_q1.png', full_page=True); await big(s, '모의고사 풀기')
        # 잠시 멈춤 — 5분이 흘러도 남은 시간 그대로, 문제는 가림
        left0 = await s.evaluate('Math.round(mxLeft()/1000)')
        await s.click('#mxPause'); await s.wait_for_timeout(100)
        assert await s.locator('.mxpaused').count() == 1 and await s.locator('[data-mxp]').count() == 0
        await s.screenshot(path=f'{SC}/m03_mock_paused.png'); await big(s, '멈춤')
        assert await s.locator('#mxPause').count() == 0 and await s.locator('#mxResume').count() == 1
        await s.clock.fast_forward(300_000); await s.wait_for_timeout(100)
        assert abs(await s.evaluate('Math.round(mxLeft()/1000)') - left0) <= 1, '멈춘 동안 시간이 흘렀음'
        await s.click('#mxResume'); await s.wait_for_timeout(100); assert await s.locator('[data-mxp]').count() == 5
        # 1번은 맞힘(위), 2~25: 3의 배수 번호는 틀리고 25번은 답을 안 한다
        for i in range(1, 25):
            await s.click('#mxNext'); await s.wait_for_timeout(40)
            if i == 24: break
            a = await s.evaluate('mx.items[mx.i].answer'); n = i + 1
            await s.click(f'[data-mxp="{a if n % 3 else a % 5 + 1}"]'); await s.wait_for_timeout(30)
        assert await s.evaluate('mx.i') == 24 and await s.evaluate('mx.picks.filter(Boolean).length') == 24
        assert await s.locator('.omrgrid button').count() == 25 and await s.locator('.omrgrid button.on').count() == 24
        await s.click('[data-mxgo="11"]'); await s.wait_for_timeout(80); assert await s.evaluate('mx.i') == 11
        await s.screenshot(path=f'{SC}/m04_mock_q12.png', full_page=True)
        await s.evaluate('window.__askManual = true')
        await s.click('#mxSubmit'); await s.wait_for_timeout(150)
        assert '답하지 않은 문항이 1개' in await s.inner_text('#ask'); await s.click('#askYes'); await s.wait_for_timeout(300)
        await s.evaluate('window.__askManual = false')
        exp = await s.evaluate("mx.items.reduce((a, q, i) => a + (i === 24 || (i + 1) % 3 === 0 ? 0 : q.points), 0)")
        assert await s.evaluate('mx.res.score') == exp
        bigt = await s.inner_text('.result .big'); assert bigt.replace('\n', '').replace(' ', '').startswith(f"{exp:g}/50"), (bigt, exp)
        rec = await s.evaluate("S.mk['1'].slice(-1)[0]")
        assert rec['d'] == '2026-10-06' and rec['s'] == exp and rec['w'] == [3, 6, 9, 12, 15, 18, 21, 24, 25] and rec['t'] < 2400, rec
        assert len(json.dumps(await s.evaluate("S.mk"))) < 200, '모의고사 기록이 너무 큼'
        # 처방: 틀린 문항의 소단원들(배점 많이 놓친 곳부터)
        rx = await s.evaluate("rxList(mx.items.map((q, i) => ({ q, n:i + 1, i })).filter(e => !mx.res.ok[e.i]), q => q.points).map(e => e.l)")
        wl = await s.evaluate("[...new Set(mx.items.filter((q, i) => !mx.res.ok[i]).flatMap(q => q.lessons))]")
        assert sorted(rx) == sorted(wl) and await s.locator('.rxrow').count() == len(rx), (rx, wl)
        assert '다시 볼 소단원' in await s.inner_text('#v-bank') and await s.locator('[data-mxr]').count() == 25
        assert await s.evaluate("S.wrong.filter(w => /^M1-/.test(w.b)).length") == 9
        await big(s, '모의고사 결과'); await s.screenshot(path=f'{SC}/m05_mock_result.png'); await s.screenshot(path=f'{SC}/m05_mock_result_full.png', full_page=True)
        await s.click('[data-mxr="2"]'); await s.wait_for_timeout(150)
        v = await s.inner_text('#v-bank'); assert '정답' in v and await s.locator('.verdict p').count() == 1 and await s.locator('.opt.bad').count() == 1
        await s.screenshot(path=f'{SC}/m06_mock_review.png', full_page=True); await big(s, '모의고사 해설')
        await s.click('#mxRvNext'); await s.wait_for_timeout(80); assert await s.evaluate('mx.rv') == 3
        await s.click('#mxBackRes'); await s.wait_for_timeout(80)
        # 처방 → 그 소단원 문제 풀기(보통 풀이로, 모의고사는 닫힘)
        await s.locator('.rxrow [data-drill]').first.click(); await s.wait_for_timeout(200)
        assert await s.evaluate('mx === null && bs && bs.items.length > 0 && bs.items.every(q => !isUM(q))')
        await s.click('#bankQuit'); await s.wait_for_timeout(150)
        # 40분이 다 되면 저절로 제출 · 그만두기는 기록하지 않는다
        await s.click('[data-um="mock"]'); await s.wait_for_timeout(150); await s.click('[data-mstart="2"]'); await s.wait_for_timeout(200)
        await s.click('[data-mxp="1"]'); await s.wait_for_timeout(50)
        await s.clock.fast_forward(40 * 60_000 + 2000); await s.wait_for_timeout(300)
        assert await s.evaluate('mx.done && mx.res.auto') and len(await s.evaluate("S.mk['2']")) == 1
        assert '40분이 지나' in await s.inner_text('#v-bank')
        await s.click('#mockClose2'); await s.wait_for_timeout(100)
        await s.click('[data-um="mock"]'); await s.wait_for_timeout(150)
        assert '지난 기록' in await s.inner_text('#v-bank')
        await s.click('#mockTimer'); await s.wait_for_timeout(80); assert await s.evaluate('S.mt') is False
        await s.click('[data-mstart="2"]'); await s.wait_for_timeout(150); assert '타이머 끔' in await s.inner_text('.mxbar')
        await s.click('#mockQuit'); await s.wait_for_timeout(300)
        assert await s.evaluate('mx') is None and len(await s.evaluate("S.mk['2']")) == 1, '그만둔 응시가 기록됨'
        await s.click('#umBack'); await s.wait_for_timeout(100)

        # ───────── 3) 시험처럼(문항당 96초) ─────────
        await s.click('#bankTimed'); await s.wait_for_timeout(100); assert await s.evaluate('S.bt') is True
        await s.click('[data-bsel="type"][data-val="ox"]'); await s.wait_for_timeout(80); await s.click('[data-bsel="n"][data-val="10"]')
        await s.click('#bankStart'); await s.wait_for_timeout(200)
        assert await s.evaluate('bs.timed') and (await s.inner_text('#qClock')).startswith(('1:36', '1:35'))
        await s.screenshot(path=f'{SC}/t01_timed.png')
        sid = await s.evaluate('bs.items[0].id')
        await s.clock.fast_forward(50_000); await s.wait_for_timeout(120); assert await s.evaluate('bs.i') == 0
        assert (await s.inner_text('#qClock')).startswith(('0:4', '0:5'))
        await s.clock.fast_forward(47_000); await s.wait_for_timeout(200)
        assert await s.evaluate('bs.i') == 1 and await s.evaluate(f"S.bh['{sid}']") == 'x', '96초가 지나도 넘어가지 않음'
        assert await s.evaluate(f"S.wrong.some(w => w.b === '{sid}' && !w.cleared && w.p === '시간 넘김')")
        for i in range(1, 10):
            await answer(s, True); await s.wait_for_timeout(40)
            assert await s.locator('#qClock').count() == 0      # 채점 뒤에는 시계가 멈춘다
            await s.click('#bankNext'); await s.wait_for_timeout(60)
        r = await s.inner_text('#v-bank'); assert '시간을 넘긴 문제 1' in r and '9' in await s.inner_text('.result .big'), r[:300]
        assert await s.evaluate('bs.tm.length') == 10
        await s.screenshot(path=f'{SC}/t02_timed_result.png', full_page=True)
        await s.click('#bankQuit2'); await s.wait_for_timeout(100)
        await s.click('#bankTimed'); await s.wait_for_timeout(80); await s.click('#bankStart'); await s.wait_for_timeout(150)
        assert await s.evaluate('!bs.timed') and await s.locator('#qClock').count() == 0

        # ───────── 4) 손님 — 잠김 · 차분한 이용권 안내 ─────────
        g = await page()
        await g.click('#goGuest'); await g.wait_for_timeout(400)
        await g.click('.tab[data-v="bank"]'); await g.wait_for_function('MORE.ok', timeout=15000); await g.wait_for_timeout(300)
        assert not await g.evaluate('fullAccess()') and await g.locator('.umsec .lockb').count() == 2
        await g.click('[data-um="mock"]'); await g.wait_for_timeout(250)
        sh = await g.inner_text('#sheet'); assert '전 범위에서 열립니다' in sh and '이용권' in sh, sh
        assert await g.evaluate('mx === null && umPick === null')
        await g.screenshot(path=f'{SC}/g01_guest_lock.png'); await big(g, '이용권 안내')
        await g.click('#sheetClose'); await g.wait_for_timeout(100)
        await g.click('[data-um="unit"]'); await g.wait_for_timeout(200); assert '대단원 마무리는' in await g.inner_text('#sheet'); await g.click('#sheetClose')
        await g.evaluate("startUnit && (umPick = 'unit', renderBank())"); assert await g.evaluate('umPick') is None, '손님이 단원 고르기 화면을 엶'
        assert await g.evaluate('bankPool().every(q => !isUM(q))')

        # ───────── 5) 어두운 화면 ─────────
        d = await page('dark'); await login(d)
        await d.locator('.umsec').scroll_into_view_if_needed(); await d.screenshot(path=f'{SC}/d01_bank_entries.png')
        await d.click('[data-um="unit"]'); await d.wait_for_timeout(200); await d.screenshot(path=f'{SC}/d02_unit_pick.png')
        await d.click('#umBack'); await d.click('[data-um="mock"]'); await d.wait_for_timeout(150); await d.click('[data-mstart="1"]'); await d.wait_for_timeout(200)
        await d.click('[data-mxgo="11"]'); await d.wait_for_timeout(100); await d.screenshot(path=f'{SC}/d03_mock_q12.png')
        for i in range(25):
            await d.evaluate(f"mx.picks[{i}] = mx.items[{i}].answer % 5 + ({i} % 2 ? 0 : 1) || 1")
        await d.evaluate('mockSubmit(false)'); await d.wait_for_timeout(250); await d.screenshot(path=f'{SC}/d04_mock_result.png')

        assert not errs, errs
        print('UNIT·MOCK E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
