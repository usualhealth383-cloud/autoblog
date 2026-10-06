#!/usr/bin/env python3
"""첫 진입 가볍게 E2E(2026-10-07 디자인 감사 #15 — 원장님: 첫 진입에 면책·경고·동의 벽 없이, 편안하게, 너무 자세하지 않게).

· 소개 3장: 그림 판이 화면 높이의 40 % 넘게 · 세 장 같은 높이 · 제목 바로 위(빈 공간 없음) · 글은 한 장에 한 문장(해요체) · 2장은 복습 규칙 한 문장(SRS_RULE)
· 시작 화면: 히어로는 그림 + 헤드라인 하나 · 숫자는 한 줄('개념 140 · 문제 … · 자료 탐구 …') · 아래 안내 한 문장 · 한 화면에 다 보임
· 가입 뒤 환영(학생): 한 문장 · 번호 목록 없음
· 이야기 첫 진입: 규칙 상자 대신 빈 상태 그림 + '첫 질문을 올려 보세요' + 접힌 한 줄 '함께 쓰는 규칙 3가지'(펼치면 3줄) · 글쓰기 시트 안에는 규칙 그대로
· 가로 넘침·말줄임 없음 · 밝은/어두운 스크린샷

전제: docs/parkchan 이 :8765 에 떠 있다.   사용: python3 tools/e2e_firstlook.py [--shots 폴더]
"""
import asyncio, sys, os, re
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import auto_yes, signup, member
APP = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html') + '?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_firstlook'; os.makedirs(SC, exist_ok=True)
SENT = re.compile(r'[.?!]\s|[.?!]$')


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        errs = []
        for theme in ('light', 'dark'):
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, color_scheme=theme)
            pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            await auto_yes(pg)
            await pg.goto(APP); await pg.wait_for_timeout(700)

            async def tidy(where):
                r = await pg.evaluate("""(() => ({ sw:document.scrollingElement.scrollWidth, vw:innerWidth,
                  ell:[...document.querySelectorAll('main *')].filter(e => getComputedStyle(e).textOverflow === 'ellipsis' && e.offsetParent).map(e => e.className) }))()""")
                assert r['sw'] <= r['vw'] and not r['ell'], (where, r)

            # ───────── 소개 3장 ─────────
            assert await pg.evaluate('authMode') == 'intro'
            hs = []
            for i in range(3):
                r = await pg.evaluate("""(() => { const a = document.querySelector('.intro .art').getBoundingClientRect(), h = document.querySelector('.intro h1').getBoundingClientRect();
                  return { ah:a.height, gap:h.top - a.bottom, p:document.querySelector('.intro p').textContent, n:document.querySelectorAll('.intro p').length, vh:innerHeight }; })()""")
                hs.append(round(r['ah']))
                assert r['ah'] >= r['vh'] * 0.4, (i, '그림 판이 작음', r)
                assert 0 <= r['gap'] <= 30, (i, '그림과 제목 사이가 비어 있음', r)
                assert r['n'] == 1 and len(SENT.findall(r['p'])) == 1 and r['p'].rstrip().endswith('요.'), (i, '한 장에 한 문장(해요체)이 아님', r['p'])
                if i == 1: assert r['p'] == await pg.evaluate('SRS_RULE'), '2장이 복습 규칙 문장과 다름'
                await tidy(f'소개 {i+1}'); await pg.screenshot(path=f'{SC}/i0{i+1}_intro_{theme}.png')
                await pg.click('#introNext'); await pg.wait_for_timeout(250)
            assert len(set(hs)) == 1, ('세 장 그림 높이가 다름', hs)

            # ───────── 시작 화면 ─────────
            st = await pg.evaluate("""(() => { const v = document.querySelector('.auth.start'); return { h1:v.querySelectorAll('h1').length, art:v.querySelectorAll('.art svg').length,
              mark:v.querySelectorAll('.mark').length, tiles:v.querySelectorAll('.facts div').length, facts:(v.querySelector('.facts')||{}).textContent || '',
              fine:(v.querySelector('.fine')||{}).textContent || '', lead:(v.querySelector('.lead')||{}).textContent || '', bottom:document.getElementById('goGuest').getBoundingClientRect().bottom }; })()""")
            assert st['h1'] == 1 and st['art'] == 1 and st['mark'] == 0 and st['tiles'] == 0, st
            assert re.fullmatch(r'개념 \d+ · 문제 [\d,]+ · 자료 탐구 \d+', st['facts'].strip()), st['facts']
            assert len(SENT.findall(st['lead'])) == 1 and len(SENT.findall(st['fine'])) == 1, st
            assert st['bottom'] <= 844, ('둘러보기 버튼이 첫 화면 밖', st)
            await tidy('시작'); await pg.screenshot(path=f'{SC}/i04_start_{theme}.png')

            # ───────── 가입 → 환영(학생 한 문장) ─────────
            await signup(pg, '첫만남', f'first-{theme}@look.kr', welcome=False)
            assert await pg.evaluate('authMode') == 'welcome'
            wl = await pg.evaluate("(() => ({ next:document.querySelectorAll('.welcome .next').length, lead:document.querySelector('.welcome .lead').textContent }))()")
            assert wl['next'] == 0 and len(SENT.findall(wl['lead'])) == 1 and '오늘 할 일' in wl['lead'], wl
            await pg.screenshot(path=f'{SC}/i05_welcome_{theme}.png')
            await pg.click('#welcomeGo'); await pg.wait_for_timeout(800)

            # ───────── 이야기 첫 진입 ─────────
            await member(pg)
            await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(600)
            assert await pg.locator('#v-talk .tsafe').count() == 0, '이야기 첫 화면에 규칙 상자가 펼쳐져 있음'
            if await pg.evaluate("!document.querySelector('#v-talk .pcard')"):
                t = await pg.inner_text('#v-talk .tempty'); assert '첫 질문을 올려 보세요' in t and await pg.locator('#v-talk .tempty svg').count() == 1, t
            rl = pg.locator('#v-talk details.trule')
            assert await rl.count() == 1 and not await rl.evaluate('e => e.open') and '함께 쓰는 규칙 3가지' in await rl.locator('summary').inner_text()
            sh = await rl.evaluate('e => e.getBoundingClientRect().height'); assert sh <= 52, ('접힌 규칙이 한 줄이 아님', sh)
            await tidy('이야기'); await pg.screenshot(path=f'{SC}/i06_talk_{theme}.png')
            await rl.locator('summary').click(); await pg.wait_for_timeout(150)
            assert await rl.locator('li').count() == 3 and '원문' in await rl.inner_text()
            await pg.screenshot(path=f'{SC}/i07_talk_rules_{theme}.png', full_page=True)
            # 글쓰기 시트에는 규칙이 그대로
            await pg.click('#postNew'); await pg.wait_for_timeout(300)
            if await pg.locator('#nkIn').count():   # 닉네임을 먼저 정한다
                await pg.fill('#nkIn', f'첫만남{"밝" if theme == "light" else "밤"}'); await pg.click('#nkSave'); await pg.wait_for_timeout(500)
                if not await pg.locator('.sheet .tsafe').count(): await pg.click('#postNew'); await pg.wait_for_timeout(300)
            assert '원문을 그대로 올리지 마세요' in await pg.inner_text('.sheet .tsafe'), '글쓰기 시트에 규칙이 없음'
            await pg.click('#sheetClose'); await pg.wait_for_timeout(200)
            await ctx.close()

        bad = [e for e in errs if 'favicon' not in e]
        assert not bad, bad
        print('FIRST LOOK E2E OK · 콘솔 오류', bad)


asyncio.run(main())
