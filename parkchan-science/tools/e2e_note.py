#!/usr/bin/env python3
"""공부 노트 · 달력 E2E — 로그인 전에 쓰기(틀 고르기·끼워 넣기 칩·마음·이해·쓰는 대로 저장) → 달력 점·검색 → 가입하면 계정으로 옮겨짐
→ 개념에서 노트 적기 → 시험 전 다시 읽기(소단원별·가리고 떠올리기·'아직 흐려요'만) → 지난 기록 한 장
→ 새 기기(서버)에서 이어 보기(틀·칸·마음까지) → 남(원장·다른 학생)은 못 읽음 → 지우기 → 로그아웃하면 기기에서 비움
→ 옛 노트(틀 없음)·옛 앱이 본문만 고친 노트 호환 → 밝은/어두운 390×844 화면(가로 넘침·말줄임 없음).

전제: 앱이 떠 있다(기본 :8765, 다른 포트면 PCS_APP=http://127.0.0.1:8776/index.html), --server 면 tools/testbed_up.sh 시험대(:8767).
사용: python3 tools/e2e_note.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SERVER = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon'] if SERVER else ''
BASE = os.environ.get('PCS_APP', 'http://127.0.0.1:8765/index.html')
APP = f'{BASE}?server={GW}&key={ANON}' if SERVER else f'{BASE}?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_note'; os.makedirs(SC, exist_ok=True)
HIDE_TABS = "document.getElementById('tabs').style.visibility = 'hidden'"


def rest(path, tok, method='GET', body=None):
    r = U.Request(GW + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                  headers={'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + tok, 'Prefer': 'return=representation'})
    try:
        with U.urlopen(r) as f: return f.status, json.loads(f.read() or b'null')
    except U.HTTPError as e: return e.code, e.read().decode()[:200]



async def full(pg):
    '''가볍게 쓰기(기본 한 칸) → '+ 더 쓰기'로 틀·칸·이해도가 다 보이는 화면으로(2026-10-07 원장님: 너무 자세하면 부담)'''
    if await pg.locator('#nedFull').count(): await pg.click('#nedFull'); await pg.wait_for_timeout(200)

async def layout_ok(pg, where):
    """가로 넘침 · 말줄임(text-overflow·line-clamp) · 잘린 글자 없음 — 노트 화면 안에서"""
    r = await pg.evaluate("""(() => { const root = document.querySelector(view === 'noted' ? '#v-noted' : '#v-note');
      const vis = e => e.offsetParent !== null;
      return { wide: document.scrollingElement.scrollWidth > innerWidth + 1,
        ell: [...root.querySelectorAll('*')].filter(e => vis(e) && (getComputedStyle(e).textOverflow === 'ellipsis' || getComputedStyle(e).webkitLineClamp !== 'none')).map(e => e.className),
        cut: [...root.querySelectorAll('.ncard, .ncard .nt, .ncard .b, .ntpl button, .nins button, .nfeel button, .ncheck, .nsg h2')].filter(e => vis(e) && e.scrollWidth > e.clientWidth + 1).map(e => e.className || e.tagName) }; })()""")
    assert not r['wide'] and not r['ell'] and not r['cut'], f'{where}: 넘침·말줄임 {r}'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        if SERVER: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
        async def page(dark=False, vp=(400, 820)):
            ctx = await b.new_context(viewport={'width': vp[0], 'height': vp[1]}, color_scheme='dark' if dark else 'light'); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(500); return ctx, pg
        ctx, s = await page()
        today = await s.evaluate('todayISO()')

        # ① 로그인 전(둘러보기): 오늘 화면의 일력 카드 → 달력 → 노트 쓰기
        await s.click('#goGuest'); await s.wait_for_timeout(300)
        assert await s.locator('#goNote').count() == 1, '오늘 화면에 노트 카드가 없음'
        assert str(int(today[-2:])) in await s.inner_text('#goNote .pg'), '일력에 오늘 날짜가 없음'
        await s.click('#goNote'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'note'
        assert await s.locator('.ncal .c.today.sel').count() == 1, '달력에 오늘 표시가 없음'
        await s.screenshot(path=f'{SC}/n01_calendar_empty.png', full_page=True)
        # 기본 틀은 '세 줄 요약', 첫 칸 안내는 오늘의 개념 이름으로(빈 칸 공포 없애기) · 빈 새 노트는 저장하지 않는다
        await s.click('#noteNew'); await s.wait_for_timeout(200); assert await s.evaluate('view') == 'noted'
        # 처음엔 가볍게: 한 칸 + 오늘 기분 + 완료 — 틀·이해도·날짜·교재와 견주기는 '더 쓰기' 안에
        assert await s.locator('.ned.lite').count() == 1 and await s.locator('.ned textarea').count() == 1 and await s.locator('.ntpl, [data-ngrasp], #nedCheck, #nedDate').count() == 0, '첫 쓰기 화면이 가볍지 않음'
        assert await s.locator('[data-nmood]').count() == 5 and await s.locator('#nedFull').count() == 1
        await s.screenshot(path=f'{SC}/n00_write_lite.png')
        await full(s)
        assert await s.get_attribute('[data-ntpl="line3"]', 'aria-pressed') == 'true', '기본 틀이 세 줄 요약이 아님'
        tc = await s.evaluate('todayConcept().title')
        assert tc in (await s.get_attribute('#nedF0', 'placeholder')), '첫 칸 안내에 오늘의 개념이 없음'
        assert await s.locator('#nedCnt').count() == 0, '글자 수 표시가 남아 있음'
        await s.click('#nedBack'); await s.wait_for_timeout(300)
        assert await s.locator('.ncard').count() == 0, '빈 노트가 저장됨'
        # 자유 틀(옛 쓰기 화면) → 세 줄 요약으로 바꾸면 쓴 글이 첫 칸으로
        await s.click('#noteNew'); await s.wait_for_timeout(200); await full(s); await s.click('[data-ntpl="free"]'); await s.wait_for_timeout(200)
        await s.fill('#nedTitle', '밀도와 부피'); await s.fill('#nedBody', '같은 질량이면 부피가 클수록 밀도가 작다.'); await s.wait_for_timeout(800)
        assert '저장됨' in await s.inner_text('#nedSaved'), '쓰는 대로 저장되지 않음'
        await s.click('[data-ntpl="line3"]'); await s.wait_for_timeout(300)
        assert await s.input_value('#nedF0') == '같은 질량이면 부피가 클수록 밀도가 작다.', '자유 → 세 줄로 바꿀 때 글이 첫 칸으로 안 옮겨짐'
        await s.click('#nedDone'); await s.wait_for_timeout(300)
        assert await s.locator('.ncard.t-line3').count() == 1 and await s.locator(f'.ncal .c[data-nday="{today}"] .dots i').count() >= 1, '달력에 노트 점이 없음'
        assert '남겨 뒀어요' in await s.inner_text('.ndone'), '저장한 뒤 차분한 완료 한 줄이 없음'

        # ② 끼워 넣기 칩 · 틀 바꾸기 · 마음/이해 · 쓰는 대로 저장(다시 열어도 남음)
        await s.click('#noteNew'); await s.wait_for_timeout(200); await full(s)
        await s.click('[data-nins^="c:"]'); await s.wait_for_timeout(300)
        assert tc in await s.input_value('#nedF0') and tc in await s.inner_text('#nedCs'), '개념 칩을 눌러도 첫 칸·개념에 안 들어감'
        await s.click('#nedF1'); await s.keyboard.type('시간과 공간이 있어야 사건을 적는다'); await s.wait_for_timeout(100)
        ans = await s.evaluate("Object.values(todayConcept().blanks)[0]")
        await s.click('[data-nins^="b:"]'); await s.wait_for_timeout(300)
        f1 = await s.input_value('#nedF1'); assert ans in f1 and f1.startswith('시간과 공간이 있어야'), f'빈칸 칩이 쓰던 칸(2번)에 안 들어감: {f1}'
        await s.screenshot(path=f'{SC}/n02_chip_insert.png', full_page=True)
        await s.click('[data-ntpl="cornell"]'); await s.wait_for_timeout(300)
        assert f1 == await s.input_value('#nedF1'), '틀을 바꾸니 칸 글이 사라짐'
        await s.fill('#nedF0', ''); await s.click('#nedF0'); k2 = await s.evaluate("Object.keys(todayConcept().blanks)[1] || Object.keys(todayConcept().blanks)[0]")
        await s.click(f'[data-nins="b:{await s.evaluate("todayConcept().id")}:{k2}"]'); await s.wait_for_timeout(300)
        f0 = await s.input_value('#nedF0'); assert f'( {k2} )' in f0 and '들어갈 말은?' in f0, f'코넬 질문 칸에 빈칸이 질문 꼴로 안 들어감: {f0}'
        await s.click('[data-nmood="calm"]'); await s.click('[data-ngrasp="1"]'); await s.wait_for_timeout(100)
        assert await s.get_attribute('[data-nmood="calm"]', 'aria-pressed') == 'true'
        await s.click('[data-nmood="tired"]'); await s.click('[data-nmood="tired"]'); await s.click('[data-nmood="calm"]'); await s.wait_for_timeout(700)
        await s.click('#nedCheck'); await s.wait_for_timeout(300)
        assert await s.locator('.sheet .nchk .pt').count() >= 1, '교재와 견주기에 포인트가 없음'
        await s.click('#sheetClose'); await s.wait_for_timeout(200)
        nid2 = await s.evaluate('noteEd.id')
        await s.reload(); await s.wait_for_timeout(900)   # 앱이 꺼져도 쓰던 노트가 남는다(쓰는 대로 저장)
        got = await s.evaluate(f"(() => {{ const n = liveNotes().find(x => x.id === '{nid2}'); return n && [n.tpl, n.mood, n.grasp, n.parts[0], n.parts[1], n.body]; }})()")
        assert got and got[0] == 'cornell' and got[1] == 'calm' and got[2] == 1 and f'( {k2} )' in got[3] and got[4] == f1, f'다시 열었더니 쓰던 노트가 다름: {got}'
        assert got[5].startswith('질문\n'), '틀 노트의 본문(검색·내보내기용)이 칸 이름으로 이어지지 않음'
        await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
        assert await s.locator('.ncard.t-cornell').count() == 1 and '마음 · 차분' in await s.inner_text('.ncard.t-cornell'), '코넬 카드·마음이 안 보임'
        assert await s.locator('.ncard.t-cornell .ngr i.on').count() == 1
        await layout_ok(s, '노트 목록')
        # 다른 날(어제)에 개인 메모 — 마지막에 고른 틀(코넬)이 기본이므로 자유로
        y = await s.evaluate('addDays(todayISO(), -1)')
        if y[:7] != today[:7]: await s.click('[data-nmon="-1"]'); await s.wait_for_timeout(200)
        await s.click(f'[data-nday="{y}"]'); await s.wait_for_timeout(200); await s.click('#noteNew'); await s.wait_for_timeout(200); await full(s)
        assert await s.get_attribute('[data-ntpl="cornell"]', 'aria-pressed') == 'true', '마지막에 고른 틀을 기억하지 않음'
        assert await s.input_value('#nedDate') == y
        await s.click('[data-ntpl="free"]'); await s.fill('#nedBody', '엄마 생신 선물 사기 — 개인 메모'); await s.wait_for_timeout(700); await s.click('#nedDone'); await s.wait_for_timeout(300)
        # 검색
        await s.fill('#noteQ', '밀도'); await s.wait_for_timeout(200)
        assert await s.locator('.ncard').count() == 1 and '밀도와 부피' in await s.inner_text('.ncard'), '검색이 안 됨'
        assert await s.evaluate("document.activeElement.id") == 'noteQ', '검색하다 입력칸 초점이 빠짐'
        await s.fill('#noteQ', '들어갈 말은'); await s.wait_for_timeout(200); assert await s.locator('.ncard.t-cornell').count() == 1, '틀 노트의 칸 글이 검색되지 않음'
        await s.fill('#noteQ', '없는말'); await s.wait_for_timeout(200); assert await s.locator('.nempty').count() == 1
        await s.fill('#noteQ', ''); await s.wait_for_timeout(200)
        assert await s.evaluate('liveNotes().length') == 3

        # ③ 가입하면 로그인 전 노트가 계정으로 옮겨진다(틀·칸·마음 그대로)
        await s.click('#noteBack'); await s.wait_for_timeout(200); await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200)
        await s.click('#goAuth')
        await s.wait_for_timeout(300)
        await signup(s, '노트학생', 'note@t.kr')
        await s.wait_for_function('!noteSyncing && NOTES.every(n => !n.dirty)', timeout=6000)
        assert await s.evaluate('liveNotes().length') == 3, '가입했는데 노트가 사라짐'
        assert await s.evaluate(f"liveNotes().find(n => n.id === '{nid2}').tpl") == 'cornell', '가입하며 틀이 사라짐'
        assert await s.evaluate("localStorage.getItem('pcs.notes.guest')") is None, '로그인 전 노트가 기기에 남음'
        assert await s.evaluate('NOTES.every(n => !n.dirty)'), '노트가 계정에 올라가지 않음'

        # ④ 개념 상세에서 '노트에 적기' → 개념이 붙은 새 노트, 붙인 개념을 누르면 교재로
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300)
        await s.locator('.row:not(.locked)').nth(1).click(); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'detail'   # 오늘의 개념(코넬 노트에 붙음)이 아닌 개념
        cid = await s.evaluate('CONCEPTS[detailIdx].id'); ctitle = await s.evaluate('CONCEPTS[detailIdx].title')
        await s.click('#noteThis'); await s.wait_for_timeout(300)
        assert await s.evaluate('view') == 'noted' and ctitle in await s.inner_text('#nedCs'), '개념이 붙지 않음'
        assert ctitle in (await s.get_attribute('#nedF0', 'placeholder')), '개념에서 연 노트의 첫 칸 안내가 그 개념이 아님'
        await full(s); await s.click('[data-ntpl="line3"]'); await s.fill('#nedF0', '이 개념 핵심: 사건 = 언제 + 어디서'); await s.click('[data-ngrasp="3"]'); await s.wait_for_timeout(700)
        await s.click('#nedAddC'); await s.wait_for_timeout(200); await s.fill('#cpickQ', '원소'); await s.wait_for_timeout(150)
        n_pick = await s.locator('[data-ncpick]').count(); assert n_pick >= 1, '개념 찾기가 안 됨'
        await s.locator('[data-ncpick]').first.click(); await s.wait_for_timeout(700)
        assert await s.locator('#nedCs .ccp').count() == 2
        await s.screenshot(path=f'{SC}/n03_editor.png', full_page=True)
        await s.click(f'[data-copen="{cid}"]'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'detail', '붙인 개념을 눌러 교재로 못 감'
        await s.click('#noteThis'); await s.wait_for_timeout(300)
        assert '사건 = 언제' in await s.input_value('#nedF0'), '같은 날 같은 개념이면 쓰던 노트를 열어야 함'
        await s.click('#nedDone'); await s.wait_for_timeout(300)
        n4 = await s.evaluate('liveNotes().map(n => [n.tpl, n.title, n.body.slice(0, 30), n.cids])'); assert len(n4) == 4, n4
        # 노트 카드의 개념 칩 → 그 개념으로, 뒤로 가면 노트로
        await s.locator(f'.ncard [data-cgo="{cid}"]').first.click(); await s.wait_for_timeout(300)
        assert await s.evaluate('view') == 'detail' and await s.evaluate('CONCEPTS[detailIdx].id') == cid, '카드의 개념 칩이 개념으로 안 감'
        await s.click('#backList'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'note', '개념에서 뒤로 가면 노트로 와야 함'
        await s.screenshot(path=f'{SC}/n04_calendar.png', full_page=True)

        # ⑤ 시험 전 다시 읽기 — 소단원별 · 가리고 떠올리기 · '아직 흐려요'만 · 같은 소단원 노트
        await s.click('[data-nmode="sum"]'); await s.wait_for_timeout(300)
        lid = await s.evaluate(f"cById('{cid}').lessonId")
        assert await s.locator('.nsg').count() >= 2, '소단원별로 모이지 않음'
        assert await s.locator('.nsg', has_text=await s.evaluate(f"LESSONS.find(L => L.id === '{lid}').name")).locator('.ncard').count() >= 1
        assert await s.locator('.nsg', has_text='개념을 붙이지 않은 노트').count() == 1, '개념 없는 노트 묶음이 없음'
        await s.click('[data-ncover]'); await s.wait_for_timeout(300)
        nc = await s.locator('.ncov').count(); assert nc >= 1, f'가리고 떠올리기에서 가린 칸이 없음 {nc}'
        hidden_txt = await s.locator('.ncard.t-cornell .np.i1 .nt').first.is_hidden(); assert hidden_txt, '코넬 핵심이 가려지지 않음'
        await s.locator('.ncard.t-cornell .ncov').first.click(); await s.wait_for_timeout(150)
        assert await s.locator('.ncard.t-cornell .np.i1 .nt').first.is_visible(), '눌러도 가린 칸이 안 보임'
        await layout_ok(s, '시험 전 다시 읽기')
        await s.click('[data-nweak]'); await s.wait_for_timeout(200)
        assert await s.locator('.ncard').count() >= 1 and await s.evaluate("[...document.querySelectorAll('.ncard')].every(c => c.classList.contains('t-cornell'))"), "'아직 흐려요'만 거르기가 안 됨"
        await s.click('[data-nweak]'); await s.click('[data-ncover]'); await s.wait_for_timeout(200)
        await s.click('[data-nmode="cal"]'); await s.wait_for_timeout(200)
        await s.locator('.ncard', has_text='사건 = 언제').locator('[data-nopen]').first.click(); await s.wait_for_timeout(300)
        if await s.locator('#nedSame').count():
            await s.click('#nedSame'); await s.wait_for_timeout(300)
            assert await s.evaluate('noteMode') == 'sum' and await s.locator('.nsg').count() == 1, '같은 소단원 노트로 안 모임'
            await s.click('[data-nlesson=""]'); await s.wait_for_timeout(200); await s.click('[data-nmode="cal"]'); await s.wait_for_timeout(200)
        else:
            await s.click('#nedDone'); await s.wait_for_timeout(300)

        # ⑥ 지난 기록 한 장 — 지난주 오늘 쓴 노트(헷갈린 것 하나 틀)
        w7 = await s.evaluate("addDays(todayISO(), -7)")
        await s.evaluate(f"putNote({{ id:newId(), date:'{w7}', title:'', body:'', cids:[], tpl:'mix', parts:['비열이 크면 빨리 데워진다고 생각함', '비열이 크면 천천히 데워진다', '물·모래 그래프 기울기부터 보기'], mood:'stuck', grasp:2 }})")
        await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
        assert await s.locator('.npast').count() == 1 and '지난주 오늘' in await s.inner_text('.npast') and await s.locator('.npast .ncard.t-mix').count() == 1, '지난 기록 한 장이 없음'
        await layout_ok(s, '지난 기록')
        await s.click('.npast [data-ngo]'); await s.wait_for_timeout(300)
        assert await s.evaluate('noteDay') == w7 and await s.evaluate('noteMonth') == w7[:7], '그날 보기가 그 날로 안 감'
        await s.evaluate("noteDay = todayISO(); noteMonth = noteDay.slice(0,7)")
        assert await s.evaluate('liveNotes().length') == 5
        # 일정 탭에서도 달력·노트로 간다, 내 정보에도 있다
        await s.click('.tab[data-v="plan"]'); await s.wait_for_timeout(300); await s.click('#planNote'); await s.wait_for_timeout(300); assert await s.evaluate('view') == 'note'
        await s.click('#noteBack'); await s.wait_for_timeout(200); assert await s.evaluate('view') == 'plan'
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(200); assert '노트 5개' in await s.inner_text('#goNoteMe')
        # 오늘 화면 카드 미리보기
        await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(300); assert '노트 3개' in await s.inner_text('#goNote')
        await s.screenshot(path=f'{SC}/n05_today_card.png')
        # 내보내기에 틀·마음·이해가 들어간다
        ex = await s.evaluate("liveNotes().map(n => ({ 틀:NTPL[tplOf(n)].name, 마음:moodName(n.mood), 이해:NGRASP[n.grasp||0] }))")
        assert any(e['틀'] == '코넬 노트' and e['마음'] == '차분' and e['이해'] == '아직 흐려요' for e in ex), ex

        if SERVER:
            tok = await s.evaluate('SESSION.access_token')
            st, rows = rest('/rest/v1/notes?select=id,title,tpl,parts,mood,grasp', tok); assert st == 200 and len(rows) == 5, (st, rows)
            assert any(r['tpl'] == 'cornell' and r['mood'] == 'calm' and r['grasp'] == 1 and len(r['parts']) >= 2 for r in rows), f'서버에 틀·칸·마음이 안 올라감 {rows}'
            # 새 기기(같은 계정): 로그인하면 노트가 보인다(틀·칸·마음까지) · 거기서 고치면 이 기기에도
            c2, s2 = await page(dark=True)
            await s2.click('#goLogin'); await s2.fill('#lgEmail', 'note@t.kr'); await s2.fill('#lgPw', 'pass1234'); await s2.click('#lgGo'); await s2.wait_for_timeout(1500)
            await s2.click('#goNote'); await s2.wait_for_timeout(900)
            assert await s2.evaluate('liveNotes().length') == 5, '새 기기에서 노트가 안 보임'
            assert await s2.evaluate(f"(n => n && n.tpl === 'cornell' && n.mood === 'calm' && n.parts[1].length > 0)(liveNotes().find(x => x.id === '{nid2}'))"), '새 기기에서 틀·칸·마음이 안 보임'
            await s2.locator('.ncard', has_text='밀도와 부피').locator('[data-nopen]').click(); await s2.wait_for_timeout(200)
            assert await s2.get_attribute('#nedMore', 'aria-expanded') == 'true', '제목이 있는 틀 노트는 더 쓰기가 펼쳐져 있어야 함'
            await s2.fill('#nedTitle', '밀도와 부피 (고침)'); await s2.wait_for_timeout(700); await s2.click('#nedDone'); await s2.wait_for_timeout(2200)
            await s2.screenshot(path=f'{SC}/n06_dark_calendar.png', full_page=True)
            await s.click('#goNote'); await s.wait_for_timeout(1200)
            assert await s.locator('.ncard', has_text='(고침)').count() == 1, '다른 기기에서 고친 노트가 안 옴'
            # 남은 못 읽는다 — 다른 학생, 원장(마음·이해 칸 포함)
            c3, s3 = await page(); await signup(s3, '다른학생', 'other@t.kr'); await s3.wait_for_timeout(800)
            t3 = await s3.evaluate('SESSION.access_token')
            st, rows = rest('/rest/v1/notes?select=id,mood,grasp,parts', t3); assert st == 200 and rows == [], f'다른 학생이 노트를 읽음: {rows}'
            nid = rest('/rest/v1/notes?select=id', tok)[1][0]['id']
            st, r = rest('/rest/v1/notes?on_conflict=id', t3, 'POST', {'id': nid, 'date': today, 'title': '덮어쓰기', 'body': 'x', 'cids': []})
            assert st >= 400, f'남의 노트를 덮어씀: {st} {r}'
            st, r = rest(f'/rest/v1/notes?id=eq.{nid}', t3, 'PATCH', {'title': 'x', 'mood': 'meh'}); assert st == 200 and r == [], f'남의 노트를 고침: {r}'
            st, r = rest(f'/rest/v1/notes?id=eq.{nid}', t3, 'DELETE'); assert r == [], f'남의 노트를 지움: {r}'
            c4, o = await page(); await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(900)
            to = await o.evaluate('SESSION.access_token'); st, rows = rest('/rest/v1/notes?select=id,mood,grasp', to); assert rows == [], f'원장이 노트를 읽음: {rows}'
            st, rows = rest('/rest/v1/notes?select=title', tok); assert all(r['title'] != '덮어쓰기' for r in rows)
            for c in (c2, c3, c4): await c.close()

        # ⑦ 지우기(확인 시트) → 달력에서 사라짐
        await s.click('#goNote') if await s.evaluate("view") == 'today' else None
        await s.wait_for_timeout(300)
        if await s.evaluate('view') != 'note': await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
        await s.click(f'[data-nday="{y}"]') if y[:7] == today[:7] else None
        await s.wait_for_timeout(200)
        if y[:7] == today[:7]:
            await s.locator('.ncard', has_text='엄마 생신').locator('[data-nopen]').click(); await s.wait_for_timeout(200)
            await s.click('#nedDel'); await s.wait_for_timeout(1900)
            assert await s.evaluate('view') == 'note' and await s.locator('.ncard').count() == 0, '지운 노트가 남음'
            assert await s.evaluate('liveNotes().length') == 4
            if SERVER:
                st, rows = rest('/rest/v1/notes?select=id', tok); assert len(rows) == 4, f'서버에서 안 지워짐 {rows}'
        # ⑦-2 올리는 도중에 지운 노트가 되살아나지 않는다 · 하나가 계속 실패해도 나머지는 올라간다
        r = await s.evaluate("""async () => { const orig = DBX.noteSave;
            DBX.noteSave = async n => { await new Promise(r => setTimeout(r, 700)); return orig(n); };
            const a = putNote({ id:newId(), date:todayISO(), title:'지울 노트', body:'x', cids:[] }); clearTimeout(noteSyncT);
            const p = syncNotes(); await new Promise(r => setTimeout(r, 200)); removeNote(a.id); await p; clearTimeout(noteSyncT); await syncNotes();
            DBX.noteSave = orig; const srv = await DBX.notesAll();
            return { srv: srv.some(n => n.id === a.id), live: liveNotes().some(n => n.id === a.id) }; }""")
        assert r == {'srv': False, 'live': False}, f'올리는 중에 지운 노트가 되살아남: {r}'
        r = await s.evaluate("""async () => { const orig = DBX.noteSave; let bad;
            DBX.noteSave = async n => { if (n.id === bad) throw new Error('거절됨'); return orig(n); };
            const x = putNote({ id:newId(), date:todayISO(), title:'막히는 노트', body:'x', cids:[] }); bad = x.id;
            const y = putNote({ id:newId(), date:todayISO(), title:'뒤따르는 노트', body:'y', cids:[] }); clearTimeout(noteSyncT); await syncNotes();
            DBX.noteSave = orig; const srv = await DBX.notesAll(); const out = { y: srv.some(n => n.id === y.id), xDirty: NOTES.find(n => n.id === x.id).dirty, err: noteSyncErr };
            removeNote(x.id); removeNote(y.id); clearTimeout(noteSyncT); await syncNotes(); return out; }""")
        assert r['y'] and r['xDirty'] and r['err'], f'실패한 노트 하나가 나머지를 막음: {r}'
        # ⑧ 로그아웃하면 기기에서 노트를 비우고, 다시 로그인하면 돌아온다
        await s.evaluate("show('me')"); await s.wait_for_timeout(200); await s.click('#logout'); await s.wait_for_timeout(900)
        assert await s.evaluate("Object.keys(localStorage).filter(k => k.startsWith('pcs.notes.') && JSON.parse(localStorage.getItem(k)).length).length") == 0, '로그아웃했는데 노트가 기기에 남음'
        await s.click('#goLogin'); await s.fill('#lgEmail', 'note@t.kr'); await s.fill('#lgPw', 'pass1234'); await s.click('#lgGo'); await s.wait_for_timeout(1500)
        await s.wait_for_function('liveNotes().length > 0 && !noteSyncing', timeout=6000)
        assert str(await s.evaluate('liveNotes().filter(n => n.date === todayISO()).length')) + '개' in await s.inner_text('#goNote'), '로그인 뒤 오늘 카드가 노트 수로 바뀌지 않음'
        got = await s.evaluate('liveNotes().length'); assert got == (4 if y[:7] == today[:7] else 5), f'다시 로그인했는데 노트가 없음: {got} · {await s.evaluate("[view, notesOwner, !!ACC]")}'
        assert await s.evaluate(f"liveNotes().find(n => n.id === '{nid2}').tpl") == 'cornell', '다시 로그인했더니 틀이 사라짐'
        await ctx.close()

        # ⑨ 옛 노트 호환 — 틀 없는 옛 노트는 '자유'로 그대로, 옛 앱이 본문만 고친 틀 노트는 본문이 이긴다
        ctx, s = await page()
        await s.click('#goGuest'); await s.wait_for_timeout(300)
        await s.evaluate("""(() => { const t = todayISO(); localStorage.setItem('pcs.notes.guest', JSON.stringify([
            { id:'00000000-0000-4000-8000-000000000001', date:t, title:'옛 노트', body:'오늘 배운 것\\n· 옛 3줄 틀', cids:[], at:new Date().toISOString() },
            { id:'00000000-0000-4000-8000-000000000002', date:t, title:'', body:'옛 앱에서 고친 본문', cids:[], tpl:'line3', parts:['처음 칸'], mood:'calm', grasp:9, at:new Date().toISOString() } ]));
            notesOwner = null; })()""")
        await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
        assert await s.locator('.ncard.t-free').count() == 2, '옛 노트가 자유 카드로 안 보임'
        assert '옛 3줄 틀' in await s.locator('.ncard', has_text='옛 노트').inner_text(), '옛 노트 본문이 안 보임'
        assert await s.locator('.ncard', has_text='옛 앱에서 고친 본문').count() == 1 and await s.locator('.ncard', has_text='처음 칸').count() == 0, '본문과 어긋난 칸을 보여 줌'
        g = await s.evaluate("liveNotes().find(n => n.id.endsWith('2')).grasp"); assert g == 0, f'잘못된 이해 값이 남음 {g}'
        await s.locator('.ncard', has_text='옛 노트').locator('[data-nopen]').click(); await s.wait_for_timeout(300)
        assert await s.get_attribute('[data-ntpl="free"]', 'aria-pressed') == 'true' and await s.input_value('#nedBody') == '오늘 배운 것\n· 옛 3줄 틀', '옛 노트를 열면 자유 틀이어야 함'
        await s.click('#nedDone'); await s.wait_for_timeout(200)
        await ctx.close()

        # ⑩ 화면 — 390×844 밝은/어두운: 틀별 쓰기 화면 · 칩 끼워 넣기 · 노트 보기 · 모아보기 · 가리고 떠올리기 · 지난 기록
        SEED = """(() => { const t = todayISO(), c = todayConcept(), c2 = CONCEPTS[(dayIndex() + 1) % CONCEPTS.length];
          const mk = (d, tpl, parts, extra) => putNote({ id:newId(), date:d, title:'', body:'', cids:[], tpl, parts, ...extra });
          mk(t, 'line3', ['측정값은 수치와 단위를 짝으로 쓴다', '단위는 기준의 몇 배인지 알려 주는 약속이라서', '야드파운드법을 아직 쓰는 나라'], { cids:[c.id], mood:'calm', grasp:2 });
          mk(t, 'cornell', ['화성 기후 궤도선이 떨어진 까닭은?', '뉴턴·초와 파운드힘·초를 섞어 써서 4.45배 어긋남. 계산은 맞았다', '숫자가 맞아도 단위 약속이 어긋나면 틀린다'], { cids:[c.id], grasp:1 });
          mk(addDays(t, -1), 'free', [], { title:'시험 범위 메모', body:'I-01 ~ I-03 · 그림 문제 많이 나옴' });
          const q = quizFor(c); S.wrong.push({ l:q.lessonId, n:q.no, p:(q.answer % 5) + 1, iso:t, a:t, x:1, k:1, d:addDays(t, 1) }); save(S);   // 오늘 틀린 문제 하나
          mk(addDays(t, -7), 'mix', ['비열이 크면 빨리 데워진다고 생각함', '비열이 크면 천천히 데워진다', '그래프 기울기부터 보기'], { cids:[c2.id], mood:'stuck', grasp:2 }); })()"""
        for dark in (False, True):
            tag = 'D' if dark else 'L'
            ctx, s = await page(dark=dark, vp=(390, 844))
            await s.click('#goGuest'); await s.wait_for_timeout(300)
            await s.evaluate(SEED); await s.wait_for_timeout(100)
            await s.evaluate("openNotes('today', todayISO())"); await s.wait_for_timeout(400)
            await layout_ok(s, f'{tag} 노트 보기'); await s.evaluate(HIDE_TABS)
            await s.screenshot(path=f'{SC}/{tag}_10_view.png', full_page=True)
            await s.click('[data-nmode="sum"]'); await s.wait_for_timeout(300); await layout_ok(s, f'{tag} 모아보기')
            await s.screenshot(path=f'{SC}/{tag}_11_summary.png', full_page=True)
            await s.click('[data-ncover]'); await s.wait_for_timeout(200); await s.locator('.ncov').first.click(); await s.wait_for_timeout(100); await layout_ok(s, f'{tag} 가리고 떠올리기')
            await s.screenshot(path=f'{SC}/{tag}_12_cover.png', full_page=True)
            await s.click('[data-ncover]'); await s.click('[data-nmode="cal"]'); await s.wait_for_timeout(200)
            await s.locator('.npast').scroll_into_view_if_needed(); await s.wait_for_timeout(100)
            await s.screenshot(path=f'{SC}/{tag}_13_past.png')
            for k in ('line3', 'cornell', 'mix', 'free'):
                await s.click('#noteNew'); await s.wait_for_timeout(250); await full(s); await s.click(f'[data-ntpl="{k}"]'); await s.wait_for_timeout(250)
                await layout_ok(s, f'{tag} 쓰기 {k}'); await s.evaluate(HIDE_TABS)
                await s.screenshot(path=f'{SC}/{tag}_2{"0123"[["line3","cornell","mix","free"].index(k)]}_write_{k}.png', full_page=True)
                if k == 'mix':
                    await s.click('#nedF0'); await s.click('[data-nins^="w:"]'); await s.wait_for_timeout(100)
                    assert (await s.input_value('#nedF0')).startswith('틀린 문제 — ') and '(정답 ' in await s.input_value('#nedF0'), '틀린 문제 칩이 안 들어감'
                    await s.click('[data-nins^="c:"]'); await s.click('#nedF1'); await s.click('[data-nins^="b:"]'); await s.click('[data-nmood="proud"]'); await s.click('[data-ngrasp="3"]'); await s.wait_for_timeout(300)
                    await layout_ok(s, f'{tag} 칩 끼워 넣기'); await s.evaluate(HIDE_TABS)
                    await s.screenshot(path=f'{SC}/{tag}_24_chips.png', full_page=True)
                    await s.click('#nedCheck'); await s.wait_for_timeout(300); await s.screenshot(path=f'{SC}/{tag}_25_check.png'); await s.click('#sheetClose'); await s.wait_for_timeout(150)
                await s.click('#nedBack'); await s.wait_for_timeout(250)
            await ctx.close()

        assert not errs, errs
        print(f'NOTE E2E OK ({"server" if SERVER else "local"}) · 스크린샷 {SC} · 콘솔 오류', errs); await b.close()

asyncio.run(main())
