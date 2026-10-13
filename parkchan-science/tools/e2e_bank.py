#!/usr/bin/env python3
"""문제 은행·자료 탐구·그림 확대 보기 E2E (로컬 어댑터).
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤 실행 — 스크린샷은 --shots DIR 에 저장.
  cd docs/parkchan && python3 -m http.server 8765 &
  python3 tools/e2e_bank.py --shots /tmp/shots
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv else '/tmp/pcs-e2e-bank'
os.makedirs(SC, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); ctx = await b.new_context(viewport={'width':400,'height':820}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'ERR_' not in m.text else None)
        await auto_yes(pg)
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(600)
        await pg.click('#goLogin'); await pg.fill('#lgEmail','student@demo.kr'); await pg.fill('#lgPw','1234'); await pg.click('#lgGo'); await pg.wait_for_timeout(700)
        assert [t for t in await pg.locator('.tab').all_inner_texts()]==['오늘','교재','문제','이야기','일정','내 정보']
        await pg.click('.tab[data-v="bank"]'); await pg.wait_for_timeout(400); await pg.screenshot(path=f'{SC}/b1_bank.png', full_page=True)
        t = await pg.locator('#v-bank').inner_text(); assert '자료 탐구' in t, t[:200]
        # 전체 문항 수는 '직접 고르기' 시트 안에(docs/23 S20 — 히어로 아래 회색 줄은 숫자 하나로)
        await pg.click('#bankCustom'); await pg.wait_for_timeout(150); assert f"{await pg.evaluate('BANK.length'):,}" in await pg.locator('.sheet').inner_text(), '직접 고르기 시트에 전체 문항 수가 없음'
        await pg.click('[data-bsel="type"][data-val="ox"]'); await pg.wait_for_timeout(200); await pg.click('#bankStart'); await pg.wait_for_timeout(400)
        assert await pg.evaluate('bs && bs.items.length')==10 and await pg.evaluate('bs.items.every(q=>q.type==="ox")')
        for i in range(10):
            ans = await pg.evaluate('bs.items[bs.i].answer'); pick = ans if i%3 else ('X' if ans=='O' else 'O')
            await pg.click(f'[data-ox="{pick}"]'); await pg.wait_for_timeout(150)
            if i==0: await pg.screenshot(path=f'{SC}/b2_ox_graded.png', full_page=True)
            await pg.click('#bankNext'); await pg.wait_for_timeout(150)
        r = (await pg.locator('.result').inner_text()).replace('\n',' '); assert '6' in r, r; await pg.screenshot(path=f'{SC}/b3_result.png', full_page=True)
        assert await pg.evaluate('Object.keys(S.bh).length')==10 and await pg.evaluate('S.wrong.filter(w=>w.b).length')==4
        await pg.click('#bankRetryWrong'); await pg.wait_for_timeout(300); assert await pg.evaluate('bs.items.length')==4
        for i in range(4):
            ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.click(f'[data-ox="{ans}"]'); await pg.wait_for_timeout(120); await pg.click('#bankNext'); await pg.wait_for_timeout(120)
        # 같은 날 다시 맞힌 것은 연습일 뿐 — 간격 복습 규칙상 정리되지 않고 내일 기한 그대로(7일 넘는 간격에서 두 번 맞혀야 정리)
        assert await pg.evaluate('S.wrong.filter(w=>w.b && !w.cleared).length')==4, '같은 날 다시 맞혔다고 정리됨'
        assert await pg.evaluate("S.wrong.filter(w=>w.b).every(w => w.x===1 && w.d===addDays(todayISO(),1))"), '문제 은행 오답의 다음 복습이 내일이 아님'
        await pg.click('#bankQuit2'); await pg.wait_for_timeout(200)
        await pg.click('#bankCustom'); await pg.wait_for_timeout(150); await pg.select_option('#bankLesson','1304'); await pg.wait_for_timeout(200); await pg.click('[data-bsel="type"][data-val="mc"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.click(f'[data-bp="{ans}"]'); await pg.wait_for_timeout(150); assert '맞았어요' in await pg.locator('.verdict').inner_text(); await pg.screenshot(path=f'{SC}/b4_mc.png', full_page=True)
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('#bankCustom'); await pg.wait_for_timeout(150); await pg.click('[data-bsel="type"][data-val="blank"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[bs.i].answer'); await pg.fill('#blankIn', ans); await pg.click('#blankGo'); await pg.wait_for_timeout(150); assert '맞았어요' in await pg.locator('.verdict').inner_text()
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('#bankCustom'); await pg.wait_for_timeout(150); await pg.click('[data-bsel="type"][data-val="multi"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300); assert await pg.locator('.bogi').count()==1
        if await pg.locator('.qfig').count(): await pg.click('.qfig'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.screenshot(path=f'{SC}/b5_zoom.png'); await pg.click('#fvClose')
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        # 합답형 ㄱㄴㄷ 판정 한 줄 — 해설 문장의 'ㄱ (옳음) …'·'ㄴ (틀림 →) …'을 보기마다 나눠 그린다(나뉘지 않는 문항은 지금처럼)
        st = await pg.evaluate("(() => { const m = BANK.filter(q => q.type === 'multi'); const sp = m.filter(q => multiSplit(q)); return [m.length, sp.length, sp.filter(q => q.wrong).length]; })()")
        print(f'  합답형 {st[0]}문항 중 보기별로 나뉨 {st[1]}')
        assert st[1] >= st[0] * 0.6, ('나뉘는 문항이 너무 적음 — 해설 모양이 바뀌었나', st)
        bad = await pg.evaluate("BANK.filter(q => q.type === 'multi').map(q => [q, multiSplit(q)]).filter(([q, sp]) => sp && sp.rows.some(r => r.ok !== new Set(String(q.choices[q.answer-1]).match(/[ㄱ-ㄹ]/g)).has(r.k))).length")
        assert bad == 0, '판정이 정답 선지와 다른 줄이 있음'
        qid = await pg.evaluate("(BANK.find(q => q.id === '1202-q8' && multiSplit(q) && openLessons().some(l => l.id === q.lessonId)) || BANK.find(q => q.type === 'multi' && multiSplit(q) && q.explain && q.wrong && openLessons().some(l => l.id === q.lessonId))).id")
        await pg.evaluate(f"startBank([BANK.find(q => q.id === '{qid}')], '')"); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[0].answer'); await pg.click(f'[data-bp="{ans % 5 + 1}"]'); await pg.wait_for_timeout(250)
        rows = await pg.locator('.expl .jd').all_inner_texts(); keys = await pg.evaluate("[...bs.items[0].source.matchAll(/(?:^|\\n)\\s*([ㄱ-ㄹ])\\s*\\./g)].map(m => m[1])")
        assert len(rows) == len(keys) >= 3 and all(r.startswith(k) for r, k in zip(rows, keys)), (rows, keys)
        assert any('틀림' in r for r in rows) and any('옳음' in r for r in rows) and await pg.locator('.wrongbox').count() == 0, rows
        await pg.screenshot(path=f'{SC}/b5b_multi_judge.png', full_page=True)
        nid = await pg.evaluate("BANK.find(q => q.type === 'multi' && !multiSplit(q) && q.explain && openLessons().some(l => l.id === q.lessonId)).id")
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.evaluate(f"startBank([BANK.find(q => q.id === '{nid}')], '')"); await pg.wait_for_timeout(300)
        ans = await pg.evaluate('bs.items[0].answer'); await pg.click(f'[data-bp="{ans}"]'); await pg.wait_for_timeout(250)
        assert await pg.locator('.expl .jd').count() == 0 and await pg.locator('.expl p').count() >= 1, '나뉘지 않는 문항이 지금처럼 그려지지 않음'
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        await pg.click('#bankCustom'); await pg.wait_for_timeout(150); await pg.click('[data-bsel="type"][data-val="essay"]'); await pg.click('#bankStart'); await pg.wait_for_timeout(300)
        await pg.fill('#essayIn','충돌 시간이 길어져 힘이 작아진다'); await pg.click('#essayShow'); await pg.wait_for_timeout(200); assert '모범 답안' in await pg.locator('.verdict').inner_text(); await pg.screenshot(path=f'{SC}/b6_essay.png', full_page=True)
        await pg.click('[data-ess="맞음"]'); await pg.wait_for_timeout(200); assert await pg.evaluate('S.stats.c')>=7
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
        if await pg.locator('#labMore').count(): await pg.click('#labMore'); await pg.wait_for_timeout(150)   # 탐구는 3편 + 모두 보기(감사 #6)
        await pg.click('[data-lab="1304"]'); await pg.wait_for_timeout(400); t = await pg.locator('#v-lab').inner_text(); assert '해석의 3단계' in t and '직접 해보기' in t; await pg.screenshot(path=f'{SC}/b7_lab.png', full_page=True)
        await pg.click('[data-zoomlab]'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.click('#fvClose')
        await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(400); await pg.click('#pRead'); await pg.wait_for_timeout(300); await pg.click('[data-zoom]'); await pg.wait_for_timeout(200); assert await pg.locator('#fv').count()==1; await pg.click('#fvPlus'); await pg.click('#fvClose')
        await pg.click('.tab[data-v="list"]'); await pg.wait_for_timeout(300); i = await pg.evaluate("CONCEPTS.findIndex(c=>c.id==='1304-05')")
        ug = pg.locator(f'.ugrp:has(.row[data-i="{i}"]) .ugh')   # 교재는 대단원별로 접힌다(감사 #7) — 그 단원을 펴고
        if await ug.get_attribute('aria-expanded') != 'true': await ug.click(); await pg.wait_for_timeout(150)
        await pg.click(f'.row[data-i="{i}"]'); await pg.wait_for_timeout(400)
        assert await pg.locator('#v-detail [data-lab="1304"]').count()==1 and await pg.locator('#v-detail [data-drill="1304"]').count()==1
        await pg.click('#v-detail [data-drill="1304"]'); await pg.wait_for_timeout(300); assert await pg.evaluate('bs && bs.items.every(q=>q.lessonId==="1304")')
        await pg.click('#bankQuit'); await pg.wait_for_timeout(200)   # 풀이 중엔 탭 바가 없다(집중 모드) — 나가기로
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await pg.click('#goStats'); await pg.wait_for_timeout(800); assert '문제 은행 · 소단원별 정답률' in await pg.locator('#v-stats').inner_text()
        st_txt = await pg.locator('#v-stats').inner_text(); assert '마지막 답 기준' in st_txt and '모든 답' in st_txt, ('통계 정답률 기준이 없음(GPT 검수 #23)', st_txt[:400])
        # 심화(adv) 문항 — 앱이 고르는 곳·숙련도에서 빠지고, 직접 고르기·원장 '(심화)'에서만(2026-10-13 내용 검수)
        adv = await pg.evaluate("""(() => { const A = BANK.filter(isAdv), L = '2104', ids = new Set(A.map(q => q.id)), hit = a => a.some(q => ids.has(q.id || (q.q && q.q.id)));
            const bh0 = S.bh, one = BANK.find(q => q.lessonId === L && !isAdv(q) && !isUM(q)); S.bh = { [one.id]:'o' };   // 배운 소단원 = 2104 하나
            const recs = [...Array(30)].map(() => recPlan(true).items.map(e => e.q)).flat(), revs = [...Array(30)].map(() => reviewPlan0(true).items.filter(e => e.q).map(e => e.q)).flat(); S.bh = bh0;
            const near = recs.filter(q => q && q.lessonId === L).length;
            const ex = examPlan({ id:'a', kind:'exam', title:'t', date:addDays(todayISO(), 5), scope:{ lesson:L } }), plan = ex ? ex.rows.flatMap(r => planItems(r, ex.ls)) : [];
            const save = S.bh; S.bh = Object.fromEntries(A.map(q => [q.id, 'x'])); const ls = lessonStats()[L]; S.bh = save;
            const tq = CONCEPTS.filter(c => c.lessonId === L).map(c => todayQ(c)).filter(Boolean);
            bankSel = { book:'전체', unit:'전체', lesson:L, type:'전체', n:200, only:'전체' };
            return { n:A.length, near, rec:hit(recs), rev:hit(revs), plan:hit(plan), tq:hit(tq), ls:ls ? ls.n : 0, pick:hit(pickBank(200, true)), direct:hit(bankPool()),
              asgAll:hit(asgPool({ lesson:L, type:'전체', diff:'전체' })), asgAdv:asgPool({ lesson:L, type:'전체', diff:'심화' }).every(isAdv) && asgPool({ lesson:L, type:'전체', diff:'심화' }).length > 0,
              dqc:hit(CONCEPTS.filter(c => c.lessonId === L).flatMap(dqcItems)) }; })()""")
        assert adv['n'] >= 2 and adv['near'] >= 30 and not any(adv[k] for k in ('rec', 'rev', 'plan', 'tq', 'pick', 'asgAll', 'dqc')) and adv['ls'] == 0 and adv['direct'] and adv['asgAdv'], adv
        # 오해 OX 의 진실 짝(…-{i}o, 정답 O, pair → …-{i}x) — 있어야 하고, 어느 세트·묶음에도 짝 둘이 함께 들지 않는다(2026-10-14 문항 품질 G3)
        pr = await pg.evaluate("""(() => { const O = BANK.filter(q => /-m\\d+-\\d+o$/.test(q.id)), byId = new Map(BANK.map(q => [q.id, q]));
            const okO = O.every(q => q.type === 'ox' && q.answer === 'O' && byId.get(q.pair) && byId.get(q.pair).answer === 'X' && q.pair === q.id.slice(0, -1) + 'x');
            const both = a => { const ids = new Set(a.filter(Boolean).map(q => q.id || (q.q && q.q.id) || '')); return a.filter(Boolean).some(q => { const id = q.id || (q.q && q.q.id) || ''; return /-m\\d+-\\d+[ox]$/.test(id) && ids.has(id.slice(0, -1) + (id.endsWith('x') ? 'o' : 'x')); }); };
            const L = (O.find(q => openLessons().some(l => l.id === q.lessonId)) || {}).lessonId, P = O.find(q => q.lessonId === L), X = byId.get(P.pair);
            const bh0 = S.bh, w0 = S.wrong, sel0 = bankSel, asg0 = asgF; let hit = [], seenO = 0;
            S.bh = { [X.id]:'o' };   // 배운 소단원 = L
            for (let r = 0; r < 40; r++){
              bankSel = { book:'전체', unit:'전체', lesson:L, type:'ox', n:200, only:'전체' }; const pk = pickBank(200, true); seenO += pk.filter(q => q.answer === 'O' && q.pair).length;
              if (both(pk)) hit.push('pick'); if (both(recPlan(true).items.map(e => e.q))) hit.push('rec'); if (both(reviewPlan0(true).items.map(e => e.q || (e.w && reviewItem(e.w))))) hit.push('rev');
              asgF = { ...asg0, kind:'bank', lesson:L, type:'ox', diff:'전체', n:40 }; const dr = asgDraft(); if (dr.items && both(dr.items.map(id => byId.get(id)))) hit.push('asg');
              const ex = examPlan({ id:'p', kind:'exam', title:'t', date:addDays(todayISO(), 5), scope:{ lesson:L } }); if (ex && ex.rows.some(rw => both(planItems(rw, ex.ls)))) hit.push('plan'); }
            if (CONCEPTS.some(c => both(dqcItems(c)))) hit.push('dqc');
            // 짝 둘이 모두 오늘 복습 기한이어도 한 묶음에는 하나만(남은 하나는 다음 묶음)
            const t = todayISO(), mk = id => ({ b:id, iso:addDays(t, -3), a:addDays(t, -3), x:1, k:1, d:t }); S.wrong = [mk(X.id), mk(P.id)];
            const rv = reviewPlan0(true).items.filter(e => e.w).map(e => e.w.b);
            const sb = (startBank([X, P], ''), bs.items.map(q => q.id)); bs = null;
            S.bh = bh0; S.wrong = w0; bankSel = sel0; asgF = asg0;
            return { n:O.length, okO, hit:[...new Set(hit)], seenO, rv, sb, dp:[dropPairs([X, P]).length, dropPairs([P, X]).length, dropPairs([{ id:'a1', pair:'b1' }, { id:'b1' }]).length, dropPairs([{ id:'b1' }, { id:'a1', pair:'b1' }]).length] }; })()""")
        assert pr['n'] >= 100 and pr['okO'] and not pr['hit'] and pr['seenO'] > 0, pr
        assert len(pr['rv']) == 1 and pr['sb'] == [pr['sb'][0]] and pr['dp'] == [1, 1, 1, 1], pr
        print(f"  진실 짝 O {pr['n']}문항 · 세트마다 짝 하나만 · 복습 기한 둘 → {pr['rv']}")
        await b.close(); print('BANK OK', errs); assert not errs
asyncio.run(main())