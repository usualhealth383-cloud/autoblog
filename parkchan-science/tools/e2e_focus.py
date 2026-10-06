#!/usr/bin/env python3
"""풀이 집중 모드 · 결과 위계 · 문제 탭 히어로 · 교재 묶기 · 숙련도 네모 · 개념 상세 아래 버튼 · 작은 움직임 E2E
(2026-10-06 디자인 감사 (c) #2·5·6·7·8·10·14).

· 집중 모드: 문제 은행·오늘의 추천·오늘의 복습·대단원·모의고사·오늘의 문제를 푸는 동안 탭 바 없음, 위에 '그만 풀기'(44px 이상)와 진행 막대 8px.
  답하면(틀려도) 막대가 앞으로. 결과·해설 화면에서는 탭 바가 돌아온다. 하다 만 오늘의 복습은 '그만 풀기'로 나가도 이어 푼다
· 채점 시트: 화면 아래 붙은 시트(맞음/틀림 + 한 줄 + '다음'), '다음'에 포커스·설명 연결, 해설·합답형 판정은 시트 위 본문(.expl),
  시트가 본문 끝을 가리지 않음(본문 아래 여백 ≥ 시트 높이), 해설이 가려져 있으면 '해설 보기'
· 결과: 히어로 하나 · 점수대별 한 줄 · 칩 3개(맞힘·틀림·시간) · 주 버튼 하나(틀린 문제 바로 다시 풀기) · 점수 세기(줄임 설정이면 바로)
  모의고사: 25칸 그리드(5열, 맞힘/틀림 칸 수) · 누르면 해설 · 다시 볼 소단원은 3곳만 펼침 · 틀린 문항만 다시 풀기
· 문제 탭: 히어로 '오늘 추천 10문제' 하나(기한 된 복습 + 정답률 낮은 소단원, 같은 소단원 잇달아 안 나옴) · 조건은 '직접 고르기' 시트
  · 오답 0이면 오답 카드 없음 · 자료 탐구 3편 + 모두 보기
· 교재: 대단원 카드 6, 처음엔 오늘 단원만 펼침(접고 편 것은 기억) · 줄마다 부제 반복 없음 · 손님 안내 한 장 · 잠긴 줄도 흐리지 않음
· 숙련도: 정의(5·10·15문제, 70·90%, 복습 상자 3) 그대로 판정 · 교재·통계에 같은 네모 · 통계 범례 4줄 · 네모에 글 이름
· 개념 상세 아래: 주 버튼 하나 + 보조 한 줄 + 이전/다음 글 버튼
· 밝은/어두운 스크린샷 · 가로 넘침 없음 · 이름 없는 단추·44px 미만 단추 없음

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_focus.py [--shots 폴더]
"""
import asyncio, sys, os
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
APP = 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_focus'; os.makedirs(SC, exist_ok=True)

A11Y = """(scope) => { const vis = e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && !e.closest('[hidden],.hide') && !(e.closest('details:not([open])') && !e.closest('summary')); };
  const out = { noName:[], small:[], wide: document.documentElement.scrollWidth > innerWidth + 1, clamp:[] };
  document.querySelectorAll(scope || 'button,[role=button],a[href],summary').forEach(e => { if (!vis(e) || e.closest('#tabs,.chipbar,.tgl')) return;
    const nm = (e.getAttribute('aria-label') || e.innerText || e.title || '').trim(); if (!nm) out.noName.push(e.outerHTML.slice(0, 80));
    const r = e.getBoundingClientRect(); if (r.height < 43.5 && !e.closest('.flag,.rhythm')) out.small.push([(e.id || e.className || e.tagName) + '', Math.round(r.height)]); });
  document.querySelectorAll('main *').forEach(e => { if (!vis(e)) return; const cs = getComputedStyle(e); if (cs.textOverflow === 'ellipsis' && e.scrollWidth > e.clientWidth + 1) out.clamp.push(e.className); });
  return out; }"""


async def a11y(pg, label, scope=''):
    r = await pg.evaluate(A11Y, scope)
    assert not r['noName'] and not r['small'] and not r['wide'] and not r['clamp'], (label, r)


async def answer(pg, correct=True):
    q = await pg.evaluate("(() => { const q = bs.items[bs.i]; return { t:q.type, a:q.answer, n:(q.choices||[]).length }; })()")
    if q['t'] == 'ox':
        await pg.click(f'[data-ox="{q["a"] if correct else ("X" if q["a"] == "O" else "O")}"]')
    elif q['t'] in ('mc', 'multi'):
        await pg.click(f'[data-bp="{q["a"] if correct else q["a"] % q["n"] + 1}"]')
    elif q['t'] == 'blank':
        await pg.fill('#blankIn', str(q['a']) if correct else '모름'); await pg.click('#blankGo')
    else:
        await pg.click('#essayShow'); await pg.wait_for_timeout(80); await pg.click(f'[data-ess="{"맞음" if correct else "틀림"}"]')
    await pg.wait_for_timeout(120)


async def tabs_hidden(pg):
    return await pg.evaluate("document.getElementById('tabs').classList.contains('hide') && document.body.classList.contains('focus')")


async def run(b, theme, errs):
    t = theme[0]
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=theme, service_workers='block'); await ctx.add_init_script(NO_INTRO)
    s = await ctx.new_page(); await auto_yes(s)
    s.on('pageerror', lambda e: errs.append(f'{theme}: {e}'))
    s.on('console', lambda m: errs.append(f'{theme}: {m.text}') if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
    shot = lambda n, full=False: s.screenshot(path=f'{SC}/{t}_{n}.png', full_page=full)
    await s.goto(APP); await s.wait_for_timeout(700)

    # ── 손님: 교재 안내 한 장 · 잠긴 줄 흐리지 않음 · 문제 탭 실전처럼 잠김 표시
    await s.click('#goGuest'); await s.wait_for_timeout(400)
    await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
    assert await s.locator('#v-list .lockcard').count() == 1, '손님 잠금 안내가 한 장이 아님'
    lk = s.locator('#v-list .row.locked:visible').first
    assert await lk.count() == 1 and await lk.evaluate("e => getComputedStyle(e).opacity") == '1', '잠긴 줄이 흐림'
    await a11y(s, '손님 교재'); await shot('f01_guest_list')
    await lk.click(); await s.wait_for_timeout(200); assert await s.locator('#sheetBg').count() == 1; await s.click('#sheetClose')

    # ── 학생 로그인
    await s.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await s.wait_for_timeout(250)
    await s.click('[data-demo^="student"]'); await s.click('#lgGo'); await s.wait_for_timeout(1300)
    await s.evaluate('loadMore()'); await s.wait_for_function('MORE.ok', timeout=15000)

    # ── 숙련도 정의(감사 #8): 5·10·15문제, 70·90%, 남은 오답 복습 상자 3 이상
    lv = await s.evaluate("""(() => { const save = JSON.stringify([S.bh, S.wrong]); const L = '1104', qs = BANK.filter(q => q.lessonId === L && !isUM(q)).map(q => q.id);
      const set = (n, o) => { S.bh = {}; qs.slice(0, n).forEach((id, i) => S.bh[id] = i < o ? 'o' : 'x'); };
      const r = []; set(4, 4); r.push(masteryOf(L)); set(5, 0); r.push(masteryOf(L)); set(10, 6); r.push(masteryOf(L)); set(10, 7); r.push(masteryOf(L));
      set(15, 14); r.push(masteryOf(L)); S.wrong = [{ b:qs[14], x:2, d:todayISO(), iso:todayISO(), k:1 }]; r.push(masteryOf(L)); S.wrong[0].x = 3; r.push(masteryOf(L));
      S.bh['U1-1-q1'] = 'x'; r.push(masteryOf(L));   // 대단원 마무리 기록은 소단원 숙련도에 넣지 않는다
      [S.bh, S.wrong] = JSON.parse(save); return r; })()""")
    assert lv == [0, 1, 1, 2, 3, 2, 3, 3], ('숙련도 판정이 정의와 다름', lv)

    # 기록 만들기 — 1102 정답률 낮음(3/8), 1103 오답 하나가 오늘 기한
    await s.evaluate("""(() => { const pick = (l, n) => BANK.filter(q => q.lessonId === l && !isUM(q) && q.type !== 'essay').slice(0, n);
      pick('1101', 12).forEach((q, i) => S.bh[q.id] = i % 6 ? 'o' : 'x'); pick('1102', 8).forEach((q, i) => S.bh[q.id] = i < 3 ? 'o' : 'x');
      const w = BANK.find(q => q.lessonId === '1103' && q.type === 'ox'); S.wrong = S.wrong.filter(x => x.b !== w.id);
      S.wrong.push({ b:w.id, p:'X', iso:addDays(todayISO(), -3), a:addDays(todayISO(), -1), x:1, k:1, d:todayISO() }); window.__due = w.id; save(S); })()""")

    # ── 문제 탭: 히어로 하나 · 숫자 타일 없음 · 조건은 시트
    await s.click('.tab[data-v="bank"]'); await s.wait_for_timeout(300)
    assert await s.locator('#v-bank .rec').count() == 1 and await s.locator('#v-bank #bankRec').count() == 1, '오늘 추천 히어로가 없음'
    assert await s.locator('#v-bank .bank-top, #v-bank [data-bsel], #v-bank #bankLesson').count() == 0, '조건 칩이 시트 밖에 있음'
    hero = await s.inner_text('#v-bank .rec'); assert '다시 볼 문제' in hero and '정답률이 낮은 소단원' in hero and '02' in hero, hero
    assert await s.locator('#v-bank .wcard[data-go="wrong"]').count() == 1
    assert await s.locator('#v-bank .lab-list [data-lab]').count() == 3 and await s.locator('#labMore').count() == 1
    await s.click('#labMore'); await s.wait_for_timeout(150); assert await s.locator('#v-bank .lab-list [data-lab]').count() == await s.evaluate("LABS.filter(l => openLessons().some(x => x.id === l.lessonId)).length")
    await s.click('#labMore'); await s.wait_for_timeout(150)
    assert await s.evaluate("document.getElementById('bankRec').getBoundingClientRect().bottom") < 844, '바로 시작이 첫 화면에 없음'
    await a11y(s, '문제 탭'); await shot('f02_bank_home')
    # 직접 고르기 시트 — 칩을 눌러도 시트가 열린 채, 누른 칩에 포커스
    await s.click('#bankCustom'); await s.wait_for_timeout(200)
    assert await s.locator('#sheet [data-bsel]').count() >= 10 and await s.locator('#sheet #bankLesson').count() == 1 and await s.locator('#sheet #bankTimed').count() == 1
    await s.click('#sheet [data-bsel="type"][data-val="ox"]'); await s.wait_for_timeout(120)
    assert await s.locator('#sheetBg').count() == 1 and await s.evaluate("document.activeElement.dataset.val") == 'ox' and await s.evaluate("bankSel.type") == 'ox'
    assert await s.get_attribute('#sheet [data-bsel="type"][data-val="ox"]', 'aria-pressed') == 'true'
    await shot('f03_bank_sheet')
    await s.click('#sheet [data-bsel="type"][data-val="전체"]'); await s.click('#sheetClose'); await s.wait_for_timeout(150)

    # ── 오늘 추천 10문제: 기한 된 복습 + 약한 소단원, 같은 소단원 잇달아 안 나옴
    await s.click('#bankRec'); await s.wait_for_timeout(300)
    info = await s.evaluate("({ n:bs.items.length, kind:bs.kind, ls:bs.items.map(q => q.lessonId), ids:bs.items.map(q => q.id), due:window.__due })")
    assert info['kind'] == 'rec' and info['n'] == 10 and info['due'] in info['ids'], info
    assert info['ls'].count('1102') >= 3, ('약한 소단원 문제가 없음', info['ls'])
    assert all(a != b2 for a, b2 in zip(info['ls'], info['ls'][1:])) or len(set(info['ls'])) < 3, info['ls']
    assert await s.locator(f'#v-bank .qhead .rk').count() == (1 if info['ids'][0] == info['due'] else 0)

    # ── 집중 모드: 탭 바 없음 · 위 '그만 풀기' · 막대 8px · 답하면(틀려도) 막대가 앞으로
    assert await tabs_hidden(s), '풀이 중에 탭 바가 보임'
    qx = await s.locator('#bankQuit').bounding_box(); assert qx['y'] < 70 and qx['height'] >= 44 and '그만 풀기' in await s.inner_text('#bankQuit'), qx
    assert (await s.locator('.qtop .pbar').bounding_box())['height'] == 8
    assert await s.get_attribute('.qtop .pbar', 'aria-valuenow') == '0'
    await a11y(s, '풀이'); await shot('f04_q_open')
    await answer(s, False); await s.wait_for_timeout(400)
    assert await s.get_attribute('.qtop .pbar', 'aria-valuenow') == '1', '틀렸는데 막대가 그대로'
    w = await s.evaluate("document.querySelector('.qtop .pbar i').style.width"); assert w == '10%', w
    # 채점 시트 — 아래에 붙음 · 틀렸어요 · 다음에 포커스 · 해설은 시트 위 본문
    fb = s.locator('#v-bank .verdict.fb'); bb = await fb.bounding_box()
    assert abs(bb['y'] + bb['height'] - 844) <= 1 and bb['height'] < 844 * .45, ('시트가 아래에 붙지 않음/너무 큼', bb)
    assert '틀렸어요' in await fb.inner_text() and await fb.locator('#bankNext').count() == 1
    assert await s.evaluate("document.activeElement.id") == 'bankNext' and 'fbH' in await s.get_attribute('#bankNext', 'aria-describedby')
    pad = await s.evaluate("parseFloat(getComputedStyle(document.querySelector('main')).paddingBottom)"); assert pad >= bb['height'], (pad, bb)
    assert '내일' in await s.inner_text('#v-bank .verdict.fb .again')
    await a11y(s, '채점 시트(틀림)'); await shot('f05_q_wrong')
    await s.click('#bankNext'); await s.wait_for_timeout(200)
    await answer(s, True); await s.wait_for_timeout(200)
    assert '맞았어요' in await s.inner_text('#v-bank .verdict.fb') and await s.locator('#v-bank .verdict.fb .ck').count() == 1, '맞힘 체크가 없음'
    await shot('f06_q_right')
    # 해설이 시트 아래로 가려졌으면 '해설 보기' → 해설로
    await s.evaluate("startBank([BANK.find(q => q.id === '1202-q8')], '연습')"); await s.wait_for_timeout(250)
    a = await s.evaluate('bs.items[0].answer'); await s.click(f'[data-bp="{a % 5 + 1}"]'); await s.wait_for_timeout(250)
    assert await s.locator('#v-bank .expl .jd').count() >= 3 and await s.locator('#v-bank .verdict.fb .jd').count() == 0, '합답형 판정이 해설 칸에 없음'
    if await s.locator('#fbExpl:visible').count():
        await s.click('#fbExpl'); await s.wait_for_timeout(600)
        top, lim = await s.evaluate("[document.querySelector('#v-bank .expl').getBoundingClientRect().top, innerHeight - document.querySelector('#v-bank .verdict.fb').offsetHeight]"); assert 40 < top < lim - 40, (top, lim)
    await shot('f07_multi_expl')
    await s.click('#bankNext'); await s.wait_for_timeout(300)
    assert not await tabs_hidden(s), '결과 화면에 탭 바가 없음'
    await s.click('#bankQuit2'); await s.wait_for_timeout(200)

    # ── 결과 위계: 10문제 중 7 맞힘
    await s.evaluate("startBank(BANK.filter(q => q.type === 'ox' && q.lessonId === '1101').slice(0, 10), '')"); await s.wait_for_timeout(200)
    for i in range(10):
        await answer(s, i not in (2, 5, 8))
        await s.click('#bankNext'); await s.wait_for_timeout(60 if i < 9 else 120)
    big = s.locator('#v-bank .result .cu')
    if t == 'l': assert await big.inner_text() != '7', '점수가 세어 올라가지 않음'
    await s.wait_for_timeout(800); assert await big.inner_text() == '7' and '7 / 10' in await s.inner_text('#v-bank .result .big .sr')
    assert await s.locator('#v-bank .result').count() == 1
    assert await s.locator('#v-bank .rchips li').all_inner_texts() and [x.split('\n')[0] for x in await s.locator('#v-bank .rchips li').all_inner_texts()] == ['맞힘', '틀림', '시간']
    assert '거의 다 왔어요' in await s.inner_text('#v-bank .rline')
    assert await s.locator('#v-bank .btn').count() == 1 and await s.locator('#v-bank .btn#bankRetryWrong').count() == 1, '결과 주 버튼이 하나가 아님'
    assert await s.locator('#v-bank .rwrong li').count() == 3 and '정답' in await s.inner_text('#v-bank .rwrong')
    await a11y(s, '결과'); await shot('f08_result', True)
    await s.click('#bankRetryWrong'); await s.wait_for_timeout(200); assert await s.evaluate('bs.items.length') == 3
    for i in range(3):
        await answer(s, True); await s.click('#bankNext'); await s.wait_for_timeout(80)
    assert '전부 맞았어요' in await s.inner_text('#v-bank .rline') and await s.locator('#v-bank #bankRetryWrong').count() == 0
    assert await s.locator('#v-bank .btn#bankAgain').count() == 1, '전부 맞으면 새 세트가 주 버튼'
    await s.click('#bankQuit2'); await s.wait_for_timeout(200)

    # ── 오늘의 복습: 그만 풀기로 나가도 이어서
    await s.evaluate("show('today')"); await s.wait_for_timeout(300)
    if await s.locator('#revStart').count():
        await s.click('#revStart'); await s.wait_for_timeout(250); assert await tabs_hidden(s)
        await answer(s, True); await s.click('#bankNext'); await s.wait_for_timeout(100); i0 = await s.evaluate('bs.i')
        await s.click('#bankQuit'); await s.wait_for_timeout(250); assert await s.evaluate('view') == 'today' and not await tabs_hidden(s)
        if i0 < await s.evaluate('revHold ? revHold.items.length : 0'):
            await s.click('#revStart'); await s.wait_for_timeout(250); assert await s.evaluate('bs.i') == i0, '하다 만 복습을 이어 풀지 못함'
            await s.click('#bankQuit'); await s.wait_for_timeout(200)

    # ── 오늘의 문제도 집중 모드 + 시트
    await s.evaluate("qState = null; show('quiz')"); await s.wait_for_timeout(250); assert await tabs_hidden(s)
    a = await s.evaluate('qState.q.answer'); await s.click(f'#v-quiz .opt[data-p="{a}"]'); await s.wait_for_timeout(200)
    assert '맞았어요' in await s.inner_text('#v-quiz .verdict.fb') and await s.evaluate("document.activeElement.id") == 'grade'
    await shot('f09_quiz_sheet'); await s.click('#backToday'); await s.wait_for_timeout(250)
    assert not await tabs_hidden(s)

    # ── 모의고사: 풀이 중 집중 모드 → 결과 25칸 그리드 · 처방 3곳 · 틀린 문항만 다시
    await s.evaluate("startMock('1')"); await s.wait_for_timeout(250); assert await tabs_hidden(s)
    assert '그만두기' in await s.inner_text('#mockQuit') and await s.locator('.qtop .pbar').count() == 1
    await s.click('[data-mxp="2"]'); await s.wait_for_timeout(300); assert await s.get_attribute('.qtop .pbar', 'aria-valuenow') == '1'
    await s.evaluate("mx.items.forEach((q, i) => { mx.picks[i] = i < 16 ? q.answer : i < 23 ? q.answer % 5 + 1 : 0; }); mockSubmit(false)"); await s.wait_for_timeout(900)
    assert not await tabs_hidden(s)
    cells = s.locator('#v-bank .mxgrid .mxc'); assert await cells.count() == 25 and await s.locator('#v-bank .mxgrid .mxc.x').count() == 9
    xs = await s.evaluate("[...document.querySelectorAll('.mxgrid .mxc')].slice(0, 6).map(e => Math.round(e.getBoundingClientRect().x))")
    assert len(set(xs[:5])) == 5 and xs[5] == xs[0], ('5열 그리드가 아님', xs)
    assert (await cells.first.bounding_box())['height'] >= 44
    rx = await s.evaluate("rxList(mx.items.map((q, i) => ({ q, n:i + 1, i })).filter(e => !mx.res.ok[e.i]), q => q.points).length")
    assert await s.locator('#v-bank .rx > .rxrow').count() == min(3, rx) and await s.locator('#v-bank .rxmore .rxrow').count() == max(0, rx - 3)
    assert [x.split('\n')[0] for x in await s.locator('#v-bank .rchips li').all_inner_texts()] == ['맞힘', '틀림', '시간']
    await a11y(s, '모의고사 결과'); await shot('f10_mock_result', True)
    await s.click('[data-mxr="20"]'); await s.wait_for_timeout(150); assert await s.evaluate('mx.rv') == 20; await s.click('#mxBackRes'); await s.wait_for_timeout(150)
    await s.click('#mxRetryWrong'); await s.wait_for_timeout(250)
    assert await s.evaluate("mx === null && bs.items.length === 9 && bs.items.every(q => q.step === 'mock')"), '틀린 문항만 다시 풀기가 아님'
    await s.click('#bankQuit'); await s.wait_for_timeout(200)

    # ── 교재: 대단원 카드 · 오늘 단원만 펼침 · 접고 편 것 기억 · 부제 반복 없음 · 숙련도 네모
    await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
    g = s.locator('#v-list .ugrp'); ng = await g.count(); assert ng == 6, ng
    assert await s.locator('#v-list .ugh[aria-expanded="true"]').count() == 1, '처음부터 여러 단원이 펼쳐짐'
    assert await s.locator('#v-list .row .s:not(.today)').count() == 0, '줄마다 부제가 반복됨'
    nl = await s.evaluate("new Set(CONCEPTS.filter(c => c.book === '1' && c.unit === 'I').map(c => c.lessonId)).size")
    assert await s.locator('#v-list .ugrp[data-ug="1-I"] .ugh .mq').count() == nl
    assert await s.locator('#v-list .ugrp[data-ug="1-I"] .lh').count() == nl
    assert await s.locator('#v-list .ugrp[data-ug="1-I"] .lh .mq.m2, #v-list .ugrp[data-ug="1-I"] .lh .mq.m1').count() >= 2
    closed = s.locator('#v-list .ugh[aria-expanded="false"]').first; key = await closed.evaluate("e => e.closest('.ugrp').dataset.ug")
    await closed.click(); await s.wait_for_timeout(150)
    assert await s.locator(f'#v-list .ugrp[data-ug="{key}"] .ugb').is_visible()
    await a11y(s, '교재'); await shot('f11_list')
    await s.reload(); await s.wait_for_timeout(900); await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
    assert await s.get_attribute(f'#v-list .ugrp[data-ug="{key}"] .ugh', 'aria-expanded') == 'true', '펼친 단원을 기억하지 못함'
    await s.fill('#listQ', '효소'); await s.wait_for_timeout(300)
    assert await s.locator('#v-list .ugh[aria-expanded="false"]').count() == 0 and 1 <= await s.locator('#v-list .row').count() <= 20
    await s.fill('#listQ', ''); await s.wait_for_timeout(200)

    # ── 통계: 같은 네모 · 범례 4줄 · 네모마다 이름
    await s.evaluate('loadMore()'); await s.wait_for_function('MORE.ok', timeout=15000)
    await s.evaluate("show('stats')"); await s.wait_for_timeout(600)
    assert await s.locator('#mqSec .mq[role="img"]').count() == await s.evaluate('LESSONS.length') and await s.locator('#mqSec .mqleg li').count() == 4
    lab = await s.get_attribute('#mqSec .mq[role="img"]', 'aria-label'); assert any(x in lab for x in ('시작 전', '익숙', '능숙', '숙달')), lab
    await s.locator('#mqSec').scroll_into_view_if_needed(); await shot('f12_stats_mastery')

    # ── 개념 상세 아래: 주 버튼 하나 + 보조 한 줄 + 이전/다음 글 버튼
    await s.evaluate("detailIdx = CONCEPTS.findIndex(c => c.lessonId === '1304' && !S.done.includes(c.id)); show('detail')"); await s.wait_for_timeout(400)
    # 안 읽은 개념: 주 버튼 = '다 읽었어요 · 공부했음'(원장님 결정 — 읽기 완료는 이 버튼으로만), 문제 풀기는 보조 줄로
    assert await s.locator('#v-detail .dact .btn').count() == 1 and await s.locator('#v-detail .dact .btn#markDone').count() == 1
    assert await s.locator('#v-detail .dsub [data-drill]').count() == 1 and await s.locator('#v-detail .dsub #noteThis').count() == 1 and await s.locator('#v-detail .dsub [data-lab]').count() == 1
    assert await s.locator('#v-detail .dnav #prevC').count() == 1 and await s.locator('#v-detail #prevC.btn, #v-detail #nextC.btn').count() == 0
    await s.locator('#v-detail .dact').scroll_into_view_if_needed(); await a11y(s, '개념 상세 아래', '#v-detail .dact button, #v-detail .dnav button'); await shot('f13_detail_bottom')
    await s.click('#markDone'); await s.wait_for_timeout(200); assert await s.locator('#v-detail .dsub .dchip').count() == 1 and await s.locator('#v-detail .dact .btn[data-drill]').count() == 1
    await ctx.close()


async def motion(b, errs):
    """줄임 동작 설정이면 점수는 바로 최종 값, 진행 막대·시트는 움직이지 않는다"""
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce', service_workers='block'); await ctx.add_init_script(NO_INTRO)
    s = await ctx.new_page(); await auto_yes(s); s.on('pageerror', lambda e: errs.append(f'motion: {e}'))
    await s.goto(APP); await s.wait_for_timeout(700)
    await s.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await s.wait_for_timeout(250)
    await s.click('[data-demo^="student"]'); await s.click('#lgGo'); await s.wait_for_timeout(1200)
    await s.evaluate('loadMore()'); await s.wait_for_function('MORE.ok', timeout=15000)
    await s.evaluate("startBank(BANK.filter(q => q.type === 'ox' && q.lessonId === '1101').slice(0, 2), '')"); await s.wait_for_timeout(200)
    await answer(s, True)
    assert await s.evaluate("getComputedStyle(document.querySelector('.qtop .pbar i')).transitionDuration") == '0s'
    assert await s.evaluate("getComputedStyle(document.querySelector('.verdict.fb')).animationName") == 'none'
    await s.click('#bankNext'); await s.wait_for_timeout(80); await answer(s, True); await s.click('#bankNext'); await s.wait_for_timeout(30)
    assert await s.inner_text('#v-bank .result .cu') == '2', '줄임 설정인데 점수가 세어 올라감'
    await ctx.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        for theme in ('light', 'dark'):
            await run(b, theme, errs)
        await motion(b, errs)
        await b.close()
        assert not errs, errs
        print('FOCUS E2E OK · 집중 모드 · 채점 시트 · 결과 · 문제 탭 · 교재 · 숙련도 · 상세 아래 버튼 · 줄임 동작 · 밝은/어두운')

asyncio.run(main())
