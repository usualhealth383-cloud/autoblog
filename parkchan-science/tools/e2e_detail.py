#!/usr/bin/env python3
"""개념 상세 E2E — 2026-10-06 개념 학습 콘텐츠 감사 보완안 2·3·4·10·11.

· 확인 문제 = 그 개념의 OX(문제 은행에서 lessonId·concept 가 같은 바로바로 체크 → 모자라면 자동 OX) · 받기 전엔 자리 표시 → 받으면 그 칸만 채움
  · 맞힘·틀림은 문제 은행과 같은 복습 상자(S.wrong 의 b) · 140개 개념 전부 대조
· 읽기 전에 O/X(myths[0].x) — 답하면 바로 피드백·접힘 · 공부한 개념엔 없음 · 기록은 오늘 하루만(pcs.pre)
· 첫 화면 순서 ①②③ → 그림 → 포인트 → [본문 자세히 읽기] · 펼침은 개념별로 이 기기에 기억(pcs.dopen) · 펼치면 본문·오해('왜?')·용어
· 용어 눌러 뜻 보기 — 단추(키보드) · 말풍선이 화면 밖으로 안 나감 · Esc 로 닫고 단추로 돌아감 · 용어 감싸기가 본문 HTML 을 깨지 않음(140개)
· 시각 단서 — 오늘의 복습·문제 은행에서 그림 없는 문항이면 그 개념 그림을 접어서(개념 그림 보기) · 그림 있는 문항·시험처럼은 없음
전제: docs/parkchan 이 떠 있다(기본 :8765).   사용: PCS_APP=http://127.0.0.1:8775/index.html python3 tools/e2e_detail.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_detail'; os.makedirs(SC, exist_ok=True)
CID = '1305-03'   # 효소 — 감사 문서 견본 A

A11Y = r"""() => { const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && e.offsetParent !== null; };
  const out = { noName: [], small: [], dup: [] };
  document.querySelectorAll('#v-detail button, #v-detail [role="button"], #ttip button, #v-bank button, #v-bank summary').forEach(e => { if (!vis(e)) return;
    const n = (e.getAttribute('aria-label') || e.textContent || '').trim(); if (!n) out.noName.push(e.className);
    const r = e.getBoundingClientRect(); if (r.height < 24 || r.width < 24){ const inline = getComputedStyle(e).display.includes('inline') && e.closest('p,li,.prose,.stem,.step .d'); if (!inline) out.small.push(`${e.className} ${Math.round(r.width)}x${Math.round(r.height)}`); } });
  const seen = {}; document.querySelectorAll('[id]').forEach(e => { if (vis(e)) seen[e.id] = (seen[e.id] || 0) + 1; });
  out.dup = Object.keys(seen).filter(k => seen[k] > 1); return out; }"""


async def a11y(pg, label):
    r = await pg.evaluate(A11Y)
    assert not r['noName'] and not r['small'] and not r['dup'], (label, r)


async def run(b, theme, errs):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=theme, service_workers='block'); await ctx.add_init_script(NO_INTRO)
    s = await ctx.new_page(); await auto_yes(s)
    s.on('pageerror', lambda e: errs.append(f'{theme}: {e}'))
    s.on('console', lambda m: errs.append(f'{theme}: {m.text}') if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
    t = theme[0]
    shot = lambda n, full=False: s.screenshot(path=f'{SC}/{t}_{n}.png', full_page=full)
    # ── ① 문제 은행이 늦게 오는 망: 확인 문제 칸은 자리 표시 → 받으면 그 칸만 채운다(화면 전체를 다시 그리지 않음)
    gate = asyncio.Event()
    async def hold(route):
        await gate.wait(); await route.continue_()
    await s.route('**/more-*.json', hold)
    await s.goto(APP + ('&' if '?' in APP else '?') + 'server='); await s.wait_for_timeout(700)
    await s.click('#goGuest'); await s.wait_for_timeout(400)
    assert await s.evaluate('MORE.ok') is False
    await s.evaluate(f"detailIdx = CONCEPTS.findIndex(c => c.id === '{CID}'); show('detail')"); await s.wait_for_timeout(300)
    assert await s.locator('#dqcBox[aria-busy="true"] .skel').count() == 1, '받기 전 확인 문제 자리 표시가 없음'
    assert await s.locator('#dqcBox [data-dqc]').count() == 0
    await s.evaluate("document.querySelector('#v-detail .dcard').dataset.keep = '1'")
    if t == 'l': await s.locator('#dqcBox').scroll_into_view_if_needed(); await shot('d00_dqc_waiting')
    gate.set(); await s.wait_for_function('MORE.ok', timeout=8000); await s.wait_for_timeout(300)
    assert await s.locator('#dqcBox [data-dqc]').count() == 6, '받은 뒤 확인 문제 3개가 채워지지 않음'
    assert await s.locator('#dThink .dthink').count() == 1 and '생각해 보기' in await s.inner_text('#dMoreBtn'), '받은 뒤 생각해 보기가 채워지지 않음(2026-10-07 나중에 받는 데이터로 옮김)'
    assert await s.evaluate("document.querySelector('#v-detail .dcard').dataset.keep") == '1', '확인 문제를 채우며 화면 전체를 다시 그림'
    await s.unroute('**/more-*.json')

    # ── ② 확인 문제가 그 개념의 문항인가 — 이 화면 + 140개 전부
    qi = await s.evaluate("""(() => { const c = CONCEPTS[detailIdx]; return [...document.querySelectorAll('#dqcBox .qi')].map(r => { const q = BANK.find(x => x.id === r.dataset.qi);
        return { id: q.id, ok: q.lessonId === c.lessonId && +q.concept === +c.no && q.type === 'ox', step: q.step, stem: q.stem }; }); })()""")
    assert len(qi) == 3 and all(x['ok'] for x in qi) and all(x['step'] == 'qc' for x in qi), qi
    assert any('소모되어 없어진다' in x['stem'] for x in qi), qi
    allc = await s.evaluate("""CONCEPTS.map(c => { const it = dqcItems(c), qc = BANK.filter(q => q.lessonId === c.lessonId && +q.concept === +c.no && q.type === 'ox' && q.step === 'qc').length,
        au = BANK.filter(q => q.lessonId === c.lessonId && +q.concept === +c.no && q.type === 'ox' && q.step === 'auto').length;
        return { id: c.id, n: it.length, want: Math.min(3, qc + au), match: it.every(q => q.lessonId === c.lessonId && +q.concept === +c.no && q.type === 'ox'),
          order: it.every((q, i) => i < Math.min(3, qc) ? q.step === 'qc' : q.step === 'auto') }; })""")
    bad = [x for x in allc if not (x['match'] and x['order'] and x['n'] == x['want'])]
    assert not bad, bad[:5]
    short = [x['id'] for x in allc if x['n'] < 3]
    # 맞힘·틀림 — 같은 복습 상자
    q0 = await s.evaluate("(() => { const q = BANK.find(x => x.id === document.querySelector('#dqcBox .qi').dataset.qi); return { id: q.id, a: q.answer }; })()")
    wrong = 'X' if q0['a'] == 'O' else 'O'
    await s.click(f'#dqcBox [data-dqc="{q0["id"]}"][data-v="{wrong}"]'); await s.wait_for_timeout(200)
    fb = await s.inner_text('#dqcBox .qi:nth-of-type(1) .fb')
    assert '아쉬워요' in fb and f'정답 {q0["a"]}' in fb and '내일' in fb, fb
    assert await s.evaluate(f"S.wrong.some(w => w.b === '{q0['id']}' && !w.cleared)"), '틀린 확인 문제가 복습 상자에 안 들어감'
    assert await s.evaluate(f"document.activeElement && document.activeElement.classList.contains('fb')"), '채점 뒤 초점이 결과로 가지 않음'
    assert await s.locator(f'#dqcBox [data-dqc="{q0["id"]}"]:disabled').count() == 2
    q1 = await s.evaluate("(() => { const r = document.querySelectorAll('#dqcBox .qi')[1]; const q = BANK.find(x => x.id === r.dataset.qi); return { id: q.id, a: q.answer }; })()")
    await s.click(f'#dqcBox [data-dqc="{q1["id"]}"][data-v="{q1["a"]}"]'); await s.wait_for_timeout(200)
    assert '맞혔어요' in await s.locator('#dqcBox .qi').nth(1).locator('.fb').inner_text()
    assert await s.evaluate(f"S.bh['{q1['id']}'] === 'o' && S.bh['{q0['id']}'] === 'x'")
    await a11y(s, '확인 문제 채점')
    await s.locator('#dqcBox').scroll_into_view_if_needed(); await shot('d04_dqc_answered')
    # 다시 그려도 이 개념 안에서는 채점이 남는다
    await s.evaluate('renderDetail()'); assert await s.locator('#dqcBox .fb').count() == 2

    # ── ③ 첫 화면 순서 · 읽기 전에
    await s.evaluate(f"localStorage.removeItem('pcs.pre'); localStorage.removeItem('pcs.dopen'); S.done = S.done.filter(x => x !== '{CID}'); show('detail')"); await s.wait_for_timeout(250)
    order = await s.evaluate("""(() => { const card = document.querySelector('#v-detail .dcard'), all = [...card.querySelectorAll('*')];
        const at = sel => all.indexOf(card.querySelector(sel)); return [at('#dPre'), at('.steps'), at('figure'), at('.point'), at('#dMoreBtn')]; })()""")
    assert all(x >= 0 for x in order) and order == sorted(order), f'첫 화면 순서가 다름: {order}'
    assert await s.locator('#dMore').is_hidden() and not await s.locator('#v-detail .prose').is_visible() and not await s.locator('#v-detail .myth').first.is_visible()
    assert await s.get_attribute('#dMoreBtn', 'aria-expanded') == 'false'
    myth = await s.evaluate('plain(CONCEPTS[detailIdx].myths[0].x)')
    assert myth in await s.inner_text('#dPre'), '읽기 전에 문장이 myths[0].x 가 아님'
    await a11y(s, '개념 상세 첫 화면')
    await shot('d01_top')
    # 틀린 답(O) → '읽으면서 이유를 찾아봐요' + 접힘
    await s.click('#dPre [data-pre="O"]'); await s.wait_for_timeout(150)
    tx = await s.inner_text('#dPre')
    assert '읽으면서 이유를 찾아봐요' in tx and await s.locator('#dPre [data-pre]').count() == 0, tx
    assert await s.evaluate("document.activeElement && document.activeElement.id === 'dPre'")
    pre = await s.evaluate("JSON.parse(localStorage.getItem('pcs.pre'))")
    assert pre['d'] == await s.evaluate('todayISO()') and pre['a'] == {CID: 'O'}, pre
    assert await s.evaluate('JSON.stringify(snapshot()).includes("pcs.pre")') is False
    await shot('d02_pre_answered')
    await s.evaluate('renderDetail()'); assert await s.locator('#dPre.done').count() == 1, '오늘 답한 것이 다시 그려도 남지 않음'
    # 다른 개념 · 맞는 답(X) → 짧게 '맞아요'
    await s.evaluate("detailIdx = CONCEPTS.findIndex(c => c.id === '1303-04'); S.done = S.done.filter(x => x !== '1303-04'); renderDetail()"); await s.wait_for_timeout(150)
    await s.click('#dPre [data-pre="X"]'); await s.wait_for_timeout(150)
    assert '맞아요' in await s.inner_text('#dPre')
    # 건너뛰기 → 사라짐
    await s.evaluate("detailIdx = CONCEPTS.findIndex(c => c.id === '1303-03'); S.done = S.done.filter(x => x !== '1303-03'); renderDetail()"); await s.wait_for_timeout(150)
    await s.click('#dPre [data-pre="s"]'); await s.wait_for_timeout(150); assert await s.locator('#dPre').count() == 0
    # 어제 기록은 쓰지 않는다 · 공부한 개념엔 없다
    await s.evaluate("localStorage.setItem('pcs.pre', JSON.stringify({ d: addDays(todayISO(), -1), a: { '1303-04': 'X' } })); renderDetail()")
    await s.evaluate("detailIdx = CONCEPTS.findIndex(c => c.id === '1303-04'); renderDetail()"); assert await s.locator('#dPre [data-pre]').count() == 3, '어제 답이 오늘 남음'
    await s.click('#markDone'); await s.wait_for_timeout(200); assert await s.locator('#dPre').count() == 0, '공부한 개념에 읽기 전에가 뜸'

    # ── ④ 본문 펼치기 — 개념별 기억(새로 열어도)
    await s.evaluate(f"detailIdx = CONCEPTS.findIndex(c => c.id === '{CID}'); show('detail')"); await s.wait_for_timeout(200)
    await s.click('#dMoreBtn'); await s.wait_for_timeout(150)
    assert await s.get_attribute('#dMoreBtn', 'aria-expanded') == 'true' and await s.locator('#v-detail .prose').is_visible()
    assert '본문 접기' in await s.inner_text('#dMoreBtn')
    assert await s.locator('#v-detail .dmyth .myth .why').first.is_visible(), "펼친 뒤 오해 카드의 '왜?'가 안 보임"
    sec = await s.evaluate("[...document.querySelectorAll('#dMore > .sec h2, #dThink > .sec h2')].map(h => h.textContent)")   # 생각해 보기·예제는 #dThink 안(나중에 받는 데이터)
    assert sec == ['본문', '생각해 보기', '자주 하는 오해', '용어'] or sec == ['본문', '생각해 보기', '예제', '자주 하는 오해', '용어'], sec   # 2026-10-06 생각해 보기·예제(보완안 8·9)
    assert await s.evaluate(f"JSON.parse(localStorage.getItem('pcs.dopen'))['{CID}']") == 1
    await a11y(s, '본문 펼침')
    await s.locator('#v-detail .dmyth').scroll_into_view_if_needed(); await shot('d03_expanded_myth')
    await s.evaluate("detailIdx = CONCEPTS.findIndex(c => c.id === '1305-02'); renderDetail()"); assert await s.locator('#dMore').is_hidden(), '다른 개념까지 펼쳐짐'
    await s.reload(); await s.wait_for_timeout(700)
    await s.evaluate(f"detailIdx = CONCEPTS.findIndex(c => c.id === '{CID}'); show('detail')"); await s.wait_for_timeout(300)
    assert await s.locator('#v-detail .prose').is_visible(), '다시 열었을 때 펼침이 기억되지 않음'

    # ── ⑤ 용어 말풍선
    keys = await s.evaluate("[...document.querySelectorAll('#v-detail .tterm')].map(b => b.textContent)")
    assert '활성화 에너지' in keys and '기질 특이성' in keys, keys
    await s.evaluate("window.scrollTo(0, 0)")
    b0 = s.locator('#v-detail .prose .tterm', has_text='활성화 에너지').first
    await b0.scroll_into_view_if_needed(); await b0.click(); await s.wait_for_timeout(150)
    tip = await s.inner_text('#ttip'); assert '에너지 언덕의 높이' in tip, tip
    assert await b0.get_attribute('aria-expanded') == 'true' and await s.get_attribute('#ttip', 'role') == 'status'
    await a11y(s, '용어 말풍선')
    await shot('d05_term_tip')
    await s.keyboard.press('Escape'); await s.wait_for_timeout(100)
    assert await s.locator('#ttip').count() == 0 and await b0.get_attribute('aria-expanded') == 'false'
    assert await s.evaluate("document.activeElement && document.activeElement.classList.contains('tterm')"), 'Esc 뒤 초점이 용어로 돌아가지 않음'
    await s.keyboard.press('Enter'); await s.wait_for_timeout(100); assert await s.locator('#ttip').count() == 1, '키보드(Enter)로 안 열림'
    await s.mouse.click(20, 420); await s.wait_for_timeout(100); assert await s.locator('#ttip').count() == 0, '바깥을 눌러도 안 닫힘'
    # 화면 밖으로 안 나간다 — 펼쳐 둔 개념 여럿의 용어를 모두 눌러 본다
    out = []
    for cid in [CID, '1101-04', '2203-04', '1201-01', '2102-02', '1303-04']:
        await s.evaluate(f"(() => {{ const i = CONCEPTS.findIndex(c => c.id === '{cid}'); dOpenSet(CONCEPTS[i].id, true); detailIdx = i; renderDetail(); }})()"); await s.wait_for_timeout(120)
        n = await s.locator('#v-detail .tterm').count()
        for k in range(n):
            bt = s.locator('#v-detail .tterm').nth(k); await bt.scroll_into_view_if_needed(); await bt.click(); await s.wait_for_timeout(40)
            bb = await s.locator('#ttip').bounding_box(); vp = await s.evaluate('({ y: window.scrollY, h: window.innerHeight, w: document.documentElement.clientWidth })')
            top = bb['y']
            if bb['x'] < 8 or bb['x'] + bb['width'] > vp['w'] - 8 or top < 0 or top + bb['height'] > vp['h']: out.append((cid, k, bb))
            await bt.click(); await s.wait_for_timeout(30)
    assert not out, f'말풍선이 화면 밖: {out[:3]}'
    # 용어 감싸기가 HTML 을 깨지 않는다(140개 · 단계·본문) · 빈칸 단추 안에 들어가지 않는다
    tf = await s.evaluate("""(() => { let bad = [], n = 0, hit = 0; CONCEPTS.forEach(c => { const keys = termKeys(c), u1 = new Set(), u2 = new Set(); let one = 0;
        [...c.steps.map(x => [x.d, u1]), ...c.body.map(p => [p, u2])].forEach(([t, u]) => { const h = rich(t), o = termify(h, keys, u); n++;
          if (o.replace(/<span class="tterm" role="button" tabindex="0" data-tt="\\d+" aria-expanded="false">(.*?)<\\/span>/g, '$1') !== h) bad.push(c.id);
          if (/class="blank"[^>]*>[^<]*<button/.test(o)) bad.push(c.id + ' 빈칸'); if (o.includes('tterm')) one = 1; });
        hit += one; }); return { bad, n, hit }; })()""")
    assert not tf['bad'], tf['bad'][:5]
    # 오늘 화면(conceptCard)은 그대로 — 읽기 전에·용어 단추·펼치기가 없다
    await s.evaluate("show('today')"); await s.wait_for_timeout(500)
    assert await s.locator('#v-today .tterm, #v-today #dPre, #v-today #dMoreBtn').count() == 0

    # ── ⑥ 시각 단서 — 문제 은행 · 오늘의 복습
    await s.evaluate("startBank([BANK.find(q => q.id === '1305-c2-2'), BANK.find(q => q.id === '1305-q11')], '')"); await s.wait_for_timeout(300)
    cue = s.locator('#v-bank .cuefig')
    assert await cue.count() == 0, '답하기 전에 그림 단서가 보임(답을 알려 줄 수 있음)'
    await s.click('#v-bank [data-ox="X"]'); await s.wait_for_timeout(200)
    assert await cue.count() == 1 and await s.evaluate("!document.querySelector('#v-bank .cuefig').open"), '그림 없는 문항에 접힌 개념 그림이 없음'
    assert '개념 그림 보기' in await s.inner_text('#v-bank .cuefig summary') and '효소' in await s.inner_text('#v-bank .cuefig summary')
    pos = await s.evaluate("(() => { const v = document.getElementById('v-bank'), all = [...v.querySelectorAll('*')]; return [all.indexOf(v.querySelector('.stem')), all.indexOf(v.querySelector('.cuefig')), all.indexOf(v.querySelector('.oxrow'))]; })()")
    assert pos == sorted(pos), pos
    await shot('d06_cue_closed')
    await s.click('#v-bank .cuefig summary'); await s.wait_for_timeout(150)
    fb = await s.locator('#v-bank .cuefig figure svg').bounding_box(); assert fb and fb['height'] <= 152 and fb['x'] >= 0 and fb['x'] + fb['width'] <= 390, fb
    await a11y(s, '문제 은행 그림 단서')
    await shot('d07_cue_open')
    await s.click('#v-bank .cuefig figure'); await s.wait_for_timeout(250); assert await s.locator('#fv').count() == 1, '단서 그림을 눌러 크게 보기가 안 열림'
    await s.click('#fvClose'); await s.wait_for_timeout(150)
    await s.click('#bankNext'); await s.wait_for_timeout(200)
    assert await s.evaluate("bs.items[bs.i].id") == '1305-q11' and await s.locator('#v-bank .cuefig').count() == 0, '그림 있는 문항에도 단서가 붙음'
    await s.evaluate("S.bt = true; startBank([BANK.find(q => q.id === '1305-c2-1')], '', true)"); await s.wait_for_timeout(200)
    assert await s.locator('#v-bank .cuefig').count() == 0, '시험처럼에서도 단서가 보임'
    await s.evaluate("S.bt = false; bs = null")
    # 오늘의 복습 — 열린 소단원의 바로바로 체크 하나를 기한 된 복습으로(그림 있는 개념)
    rq = await s.evaluate("""(() => { const q = BANK.find(q => q.step === 'qc' && openLessons().some(l => l.id === q.lessonId) && (CONCEPTS.find(c => c.lessonId === q.lessonId && +c.no === +q.concept) || {}).figure && !S.wrong.some(w => w.b === q.id));
        S.wrong.push({ b:q.id, p:'X', iso:addDays(todayISO(), -2), a:addDays(todayISO(), -1), x:1, k:1, d:todayISO() }); save(S); show('today'); return q.id; })()"""); await s.wait_for_timeout(600)
    await s.click('#revStart'); await s.wait_for_timeout(300)
    assert await s.evaluate("bs && bs.kind === 'review'")
    await s.evaluate(f"bs.i = bs.items.findIndex(q => q.id === '{rq}'); renderBankSession()"); await s.wait_for_timeout(150)
    assert await s.evaluate("bs.i") >= 0 and await s.locator('#v-bank .cuefig').count() == 0
    await s.click('#v-bank [data-ox="O"]'); await s.wait_for_timeout(200)
    assert await s.locator('#v-bank .cuefig').count() == 1, '오늘의 복습(답한 뒤)에 그림 단서가 없음'
    await s.click('#v-bank .cuefig summary'); await s.wait_for_timeout(150)
    await shot('d08_review_cue')
    await ctx.close()
    return short, tf


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        for theme in ('light', 'dark'):
            short, tf = await run(b, theme, errs)
        await b.close()
    assert not errs, errs
    print(f'확인 문제 OX 3개가 안 되는 개념 {len(short)}개(있는 만큼만): {short}')
    print(f"용어 단추가 붙는 개념 {tf['hit']}/140 · 문장 {tf['n']}개 HTML 보존")
    print('DETAIL E2E OK · 스크린샷', SC)

asyncio.run(main())
