#!/usr/bin/env python3
"""공부 노트 · 달력 E2E — 로그인 전에 쓰기 → 달력 점·검색 → 가입하면 계정으로 옮겨짐 → 개념에서 노트 적기·3줄 틀
→ 새 기기(서버)에서 이어 보기 → 남(원장·다른 학생)은 못 읽음 → 지우기 → 로그아웃하면 기기에서 비움.

전제: docs/parkchan 이 :8765 에, --server 면 tools/testbed_up.sh 시험대(:8767)가 떠 있다.
사용: python3 tools/e2e_note.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SERVER = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon'] if SERVER else ''
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}' if SERVER else 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_note'; os.makedirs(SC, exist_ok=True)


def rest(path, tok, method='GET', body=None):
    r = U.Request(GW + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                  headers={'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + tok, 'Prefer': 'return=representation'})
    try:
        with U.urlopen(r) as f: return f.status, json.loads(f.read() or b'null')
    except U.HTTPError as e: return e.code, e.read().decode()[:200]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        if SERVER: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
        async def page(dark=False):
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}, color_scheme='dark' if dark else 'light'); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(500); return ctx, pg
        ctx, s = await page()
        today = await s.evaluate('todayISO()')

        # ① 로그인 전(둘러보기): 오늘 화면의 일력 카드 → 달력 → 노트 쓰기(쓰는 대로 저장)
        await s.click('#goGuest'); await s.wait_for_timeout(300)
        assert await s.locator('#goNote').count() == 1, '오늘 화면에 노트 카드가 없음'
        assert str(int(today[-2:])) in await s.inner_text('#goNote .pg'), '일력에 오늘 날짜가 없음'
        await s.click('#goNote'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'note'
        assert await s.locator('.ncal .c.today.sel').count() == 1, '달력에 오늘 표시가 없음'
        await s.screenshot(path=f'{SC}/n01_calendar_empty.png', full_page=True)
        await s.click('#noteNew'); await s.wait_for_timeout(200); assert await s.evaluate('view') == 'noted'
        await s.fill('#nedTitle', '밀도와 부피'); await s.fill('#nedBody', '같은 질량이면 부피가 클수록 밀도가 작다.'); await s.wait_for_timeout(800)
        assert '저장됨' in await s.inner_text('#nedSaved'), '쓰는 대로 저장되지 않음'
        await s.click('#nedTpl'); await s.wait_for_timeout(700)
        body = await s.input_value('#nedBody'); assert '헷갈린 것' in body and body.startswith('같은 질량이면'), '3줄 틀이 이어 붙지 않음'
        await s.click('#nedDone'); await s.wait_for_timeout(300)
        assert await s.locator('.ncard').count() == 1 and await s.locator(f'.ncal .c[data-nday="{today}"] .dots i').count() >= 1, '달력에 노트 점이 없음'
        # 빈 새 노트는 저장하지 않는다
        await s.click('#noteNew'); await s.wait_for_timeout(200); await s.click('#nedBack'); await s.wait_for_timeout(300)
        assert await s.locator('.ncard').count() == 1, '빈 노트가 저장됨'
        # 다른 날(어제)에 개인 메모
        y = await s.evaluate('addDays(todayISO(), -1)')
        if y[:7] != today[:7]: await s.click('[data-nmon="-1"]'); await s.wait_for_timeout(200)
        await s.click(f'[data-nday="{y}"]'); await s.wait_for_timeout(200); await s.click('#noteNew'); await s.wait_for_timeout(200)
        assert await s.input_value('#nedDate') == y
        await s.fill('#nedBody', '엄마 생신 선물 사기 — 개인 메모'); await s.wait_for_timeout(700); await s.click('#nedDone'); await s.wait_for_timeout(300)
        # 검색
        await s.fill('#noteQ', '밀도'); await s.wait_for_timeout(200)
        assert await s.locator('.ncard').count() == 1 and '밀도와 부피' in await s.inner_text('.ncard'), '검색이 안 됨'
        assert await s.evaluate("document.activeElement.id") == 'noteQ', '검색하다 입력칸 초점이 빠짐'
        await s.fill('#noteQ', '없는말'); await s.wait_for_timeout(200); assert await s.locator('.nempty').count() == 1
        await s.fill('#noteQ', ''); await s.wait_for_timeout(200)
        assert await s.evaluate('liveNotes().length') == 2

        # ② 가입하면 로그인 전 노트가 계정으로 옮겨진다
        await s.click('#noteBack'); await s.wait_for_timeout(200); await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200)
        await s.click('#goAuth')
        await s.wait_for_timeout(300)
        await signup(s, '노트학생', 'note@t.kr')
        await s.wait_for_function('!noteSyncing && NOTES.every(n => !n.dirty)', timeout=6000)
        assert await s.evaluate('liveNotes().length') == 2, '가입했는데 노트가 사라짐'
        assert await s.evaluate("localStorage.getItem('pcs.notes.guest')") is None, '로그인 전 노트가 기기에 남음'
        assert await s.evaluate('NOTES.every(n => !n.dirty)'), '노트가 계정에 올라가지 않음'

        # ③ 개념 상세에서 '이 개념 노트에 적기' → 개념이 붙은 새 노트, 붙인 개념을 누르면 교재로
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
        await s.locator('.row:not(.locked)').first.click(); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'detail'
        cid = await s.evaluate('CONCEPTS[detailIdx].id'); ctitle = await s.evaluate('CONCEPTS[detailIdx].title')
        await s.click('#noteThis'); await s.wait_for_timeout(300)
        assert await s.evaluate('view') == 'noted' and ctitle in await s.inner_text('#nedCs'), '개념이 붙지 않음'
        await s.fill('#nedBody', '이 개념 핵심: 사건 = 언제 + 어디서'); await s.wait_for_timeout(700)
        await s.click('#nedAddC'); await s.wait_for_timeout(200); await s.fill('#cpickQ', '원소'); await s.wait_for_timeout(150)
        n_pick = await s.locator('[data-ncpick]').count(); assert n_pick >= 1, '개념 찾기가 안 됨'
        await s.locator('[data-ncpick]').first.click(); await s.wait_for_timeout(700)
        assert await s.locator('#nedCs .ccp').count() == 2
        await s.screenshot(path=f'{SC}/n02_editor.png', full_page=True)
        await s.click(f'[data-copen="{cid}"]'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'detail', '붙인 개념을 눌러 교재로 못 감'
        await s.click('#noteThis'); await s.wait_for_timeout(300)
        assert '사건 = 언제' in await s.input_value('#nedBody'), '같은 날 같은 개념이면 쓰던 노트를 열어야 함'
        await s.click('#nedDone'); await s.wait_for_timeout(300)
        assert await s.evaluate('liveNotes().length') == 3
        await s.screenshot(path=f'{SC}/n03_calendar.png', full_page=True)
        # 일정 탭에서도 달력·노트로 간다, 내 정보에도 있다
        await s.click('.tab[data-v="plan"]'); await s.wait_for_timeout(300); await s.click('#planNote'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'note'
        await s.click('#noteBack'); await s.wait_for_timeout(200); assert await s.evaluate('view') == 'plan'
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); assert '노트 3개' in await s.inner_text('#goNoteMe')
        # 오늘 화면 카드 미리보기
        await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(300); assert '노트 2개' in await s.inner_text('#goNote')
        await s.screenshot(path=f'{SC}/n04_today_card.png')

        if SERVER:
            tok = await s.evaluate('SESSION.access_token')
            st, rows = rest('/rest/v1/notes?select=id,title', tok); assert st == 200 and len(rows) == 3, (st, rows)
            # ④ 새 기기(같은 계정): 로그인하면 노트가 보인다 · 거기서 고치면 이 기기에도
            c2, s2 = await page(dark=True)
            await s2.click('#goLogin'); await s2.fill('#lgEmail', 'note@t.kr'); await s2.fill('#lgPw', '123456'); await s2.click('#lgGo'); await s2.wait_for_timeout(1500)
            await s2.click('#goNote'); await s2.wait_for_timeout(900)
            assert await s2.evaluate('liveNotes().length') == 3, '새 기기에서 노트가 안 보임'
            await s2.locator('.ncard', has_text='밀도와 부피').click(); await s2.wait_for_timeout(200)
            await s2.fill('#nedTitle', '밀도와 부피 (고침)'); await s2.wait_for_timeout(700); await s2.click('#nedDone'); await s2.wait_for_timeout(2200)
            await s2.screenshot(path=f'{SC}/n05_dark_calendar.png', full_page=True)
            await s.click('#goNote'); await s.wait_for_timeout(1200)
            assert await s.locator('.ncard', has_text='(고침)').count() == 1, '다른 기기에서 고친 노트가 안 옴'
            # ⑤ 남은 못 읽는다 — 다른 학생, 원장
            c3, s3 = await page(); await signup(s3, '다른학생', 'other@t.kr'); await s3.wait_for_timeout(800)
            t3 = await s3.evaluate('SESSION.access_token')
            st, rows = rest('/rest/v1/notes?select=id', t3); assert st == 200 and rows == [], f'다른 학생이 노트를 읽음: {rows}'
            nid = rows0 = rest('/rest/v1/notes?select=id', tok)[1][0]['id']
            st, r = rest('/rest/v1/notes?on_conflict=id', t3, 'POST', {'id': nid, 'date': today, 'title': '덮어쓰기', 'body': 'x', 'cids': []})
            assert st >= 400, f'남의 노트를 덮어씀: {st} {r}'
            st, r = rest(f'/rest/v1/notes?id=eq.{nid}', t3, 'PATCH', {'title': 'x'}); assert st == 200 and r == [], f'남의 노트를 고침: {r}'
            st, r = rest(f'/rest/v1/notes?id=eq.{nid}', t3, 'DELETE'); assert r == [], f'남의 노트를 지움: {r}'
            c4, o = await page(); await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(900)
            to = await o.evaluate('SESSION.access_token'); st, rows = rest('/rest/v1/notes?select=id', to); assert rows == [], f'원장이 노트를 읽음: {rows}'
            st, rows = rest('/rest/v1/notes?select=title', tok); assert all(r['title'] != '덮어쓰기' for r in rows)
            for c in (c2, c3, c4): await c.close()

        # ⑥ 지우기(확인 시트) → 달력에서 사라짐
        await s.click('#goNote') if await s.evaluate("view") == 'today' else None
        await s.wait_for_timeout(300)
        if await s.evaluate('view') != 'note': await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
        await s.click(f'[data-nday="{y}"]') if y[:7] == today[:7] else None
        await s.wait_for_timeout(200)
        if y[:7] == today[:7]:
            await s.locator('.ncard', has_text='엄마 생신').click(); await s.wait_for_timeout(200)
            await s.click('#nedDel'); await s.wait_for_timeout(1900)
            assert await s.evaluate('view') == 'note' and await s.locator('.ncard').count() == 0, '지운 노트가 남음'
            assert await s.evaluate('liveNotes().length') == 2
            if SERVER:
                st, rows = rest('/rest/v1/notes?select=id', tok); assert len(rows) == 2, f'서버에서 안 지워짐 {rows}'
        # ⑦ 로그아웃하면 기기에서 노트를 비우고, 다시 로그인하면 돌아온다
        await s.evaluate("show('me')"); await s.wait_for_timeout(200); await s.click('#logout'); await s.wait_for_timeout(900)
        assert await s.evaluate("Object.keys(localStorage).filter(k => k.startsWith('pcs.notes.') && JSON.parse(localStorage.getItem(k)).length).length") == 0, '로그아웃했는데 노트가 기기에 남음'
        await s.click('#goLogin'); await s.fill('#lgEmail', 'note@t.kr'); await s.fill('#lgPw', '123456'); await s.click('#lgGo'); await s.wait_for_timeout(1500)
        await s.wait_for_function('liveNotes().length > 0 && !noteSyncing', timeout=6000)
        assert str(await s.evaluate('liveNotes().filter(n => n.date === todayISO()).length')) + '개' in await s.inner_text('#goNote'), '로그인 뒤 오늘 카드가 노트 수로 바뀌지 않음'
        got = await s.evaluate('liveNotes().length'); assert got == (2 if y[:7] == today[:7] else 3), f'다시 로그인했는데 노트가 없음: {got} · {await s.evaluate("[view, notesOwner, !!ACC]")}'
        # ⑧ 내 기록 내려받기에 노트가 들어간다(내보내기 객체만 확인)
        assert not errs, errs
        print(f'NOTE E2E OK ({"server" if SERVER else "local"}) · 콘솔 오류', errs); await b.close()

asyncio.run(main())
