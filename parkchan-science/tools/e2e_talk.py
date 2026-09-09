#!/usr/bin/env python3
"""이야기(커뮤니티) E2E — 닉네임 · 글쓰기 · 개념 첨부 · 댓글 · 채택 · 도움됨 · 신고/가림 · 개인정보 감지 · 원장 삭제.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_talk.py --shots DIR
서버 모드도 확인하려면 mock_server.py 를 :8766 에 띄우고  --server 를 덧붙인다.
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/pcs-e2e-talk'
os.makedirs(SC, exist_ok=True)
APP = 'http://127.0.0.1:8765/index.html?server=http://127.0.0.1:8766&key=anon'

async def login(pg, who):
    await pg.evaluate("['pcs.v2','pcs.local.sid','pcs.session'].forEach(k=>localStorage.removeItem(k))")
    await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
    await pg.click('#goLogin'); await pg.click(f'[data-demo^="{who}"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); pg = await ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)

        # 로그인 전에는 읽기만 안내
        await pg.click('#goGuest'); await pg.wait_for_timeout(600)
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(400)
        assert await pg.locator('#talkLogin').count() == 1, '비로그인 안내가 없다'
        await pg.screenshot(path=f'{SC}/t0_guest.png')

        # 학생 A — 닉네임 정하고 질문 올리기
        await login(pg, 'student')
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(400)
        await pg.click('#postNew'); await pg.wait_for_timeout(400)
        assert await pg.locator('#nkIn').count() == 1, '닉네임부터 묻지 않는다'
        await pg.fill('#nkIn', '01012345678'); await pg.click('#nkSave'); await pg.wait_for_timeout(300)
        assert '연락처' in await pg.locator('#nkWarn').inner_text(), '닉네임 개인정보 검사 실패'
        await pg.fill('#nkIn', '충격량파이터'); await pg.click('#nkSave'); await pg.wait_for_timeout(600)

        # 개인정보가 든 글은 한 번 경고
        await pg.select_option('#poB', 'qna')
        await pg.fill('#poT', '충격량 그래프 넓이가 왜 충격량인가요?')
        await pg.fill('#poX', '교재 III-04 읽었는데 넓이랑 봉우리 차이가 헷갈려요. 제 번호 010-2222-3333 로 알려주세요.')
        await pg.click('#poSave'); await pg.wait_for_timeout(400)
        assert '전화번호' in await pg.locator('#poWarn').inner_text(), '전화번호 경고가 안 뜬다'
        await pg.screenshot(path=f'{SC}/t1_pii.png')
        # 주민등록번호는 아예 막힌다
        await pg.fill('#poX', '주민번호 990101-1234567 입니다')
        await pg.click('#poSave'); await pg.wait_for_timeout(400)
        assert '올릴 수 없습니다' in await pg.locator('#poWarn').inner_text(), '주민번호가 막히지 않는다'
        # 제대로 고쳐서 개념을 붙여 올린다
        await pg.fill('#poX', '교재 III-04를 읽었는데 F-t 그래프에서 넓이와 봉우리 높이가 각각 무엇을 뜻하는지 헷갈립니다.')
        await pg.select_option('#poA', 'concept:1304-05')
        await pg.click('#poSave'); await pg.wait_for_timeout(800)
        assert await pg.locator('.pcard').count() >= 1, '글이 목록에 없다'
        await pg.screenshot(path=f'{SC}/t2_list.png', full_page=True)

        # 글 열기 — 첨부한 개념이 보이고 개념 화면으로 이어진다
        await pg.click('.pcard'); await pg.wait_for_timeout(600)
        assert await pg.locator('[data-openatt]').count() == 1, '첨부 카드가 없다'
        await pg.screenshot(path=f'{SC}/t3_post.png', full_page=True)
        await pg.click('[data-openatt]'); await pg.wait_for_timeout(600)
        assert await pg.evaluate('view') == 'detail'
        assert await pg.evaluate("CONCEPTS[detailIdx].id") == '1304-05'
        # 학생 B(다른 계정)로 댓글 · 도움됨
        await pg.evaluate("['pcs.v2','pcs.local.sid'].forEach(k=>localStorage.removeItem(k))")
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
        await pg.click('#goSignup'); await pg.wait_for_timeout(400)
        await pg.fill('#suName', '김학생'); await pg.fill('#suEmail', 'b@demo.kr'); await pg.fill('#suPw', '123456')
        await pg.check('#suAgree'); await pg.click('#suGo'); await pg.wait_for_timeout(900)
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        await pg.click('.pcard'); await pg.wait_for_timeout(500)
        await pg.fill('#cIn', '넓이는 충격량(운동량 변화량), 봉우리 높이는 그 순간 최대 힘이에요.')
        await pg.click('#cGo'); await pg.wait_for_timeout(500)
        assert await pg.locator('#nkIn').count() == 1, '댓글도 닉네임을 먼저 물어야 한다'
        await pg.fill('#nkIn', '과학러버'); await pg.click('#nkSave'); await pg.wait_for_timeout(500)
        await pg.fill('#cIn', '넓이는 충격량(운동량 변화량), 봉우리 높이는 그 순간 최대 힘이에요.')
        await pg.click('#cGo'); await pg.wait_for_timeout(600)
        assert await pg.locator('.cm').count() == 1, '댓글이 안 달렸다'
        await pg.click('#pLike'); await pg.wait_for_timeout(400)
        assert '1' in await pg.locator('#pLike').inner_text()
        await pg.screenshot(path=f'{SC}/t4_comment.png', full_page=True)

        # 글쓴이(학생 A)가 댓글을 채택한다
        await login(pg, 'student')
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        await pg.click('.pcard'); await pg.wait_for_timeout(500)
        assert await pg.locator('[data-cpick]').count() == 1, '채택 버튼이 없다'
        await pg.click('[data-cpick]'); await pg.wait_for_timeout(600)
        assert await pg.locator('.cm .picked').count() == 1
        await pg.click('#talkBack'); await pg.wait_for_timeout(500)
        assert await pg.locator('.pcard .ok').count() == 1, '해결됨 표시가 없다'
        await pg.screenshot(path=f'{SC}/t5_solved.png', full_page=True)

        # 차단 — 구글 플레이가 UGC 앱에 요구하는 기능
        await pg.evaluate("['pcs.v2','pcs.local.sid'].forEach(k=>localStorage.removeItem(k))")
        await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
        await pg.click('#goLogin'); await pg.click('[data-demo^="parent"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        n_before = await pg.locator('.pcard').count()
        assert n_before >= 1
        await pg.click('.pcard'); await pg.wait_for_timeout(500)
        assert await pg.locator('#pBlock').count() == 1, '차단 버튼이 없다'
        assert await pg.locator('[data-cblock]').count() >= 1, '댓글 차단 버튼이 없다'
        await pg.click('#pBlock'); await pg.wait_for_timeout(800)
        assert await pg.evaluate('S.blocked.length') == 1, '차단이 저장되지 않았다'
        assert await pg.locator('.pcard').count() == n_before - 1, '차단한 사람 글이 그대로 보인다'
        await pg.screenshot(path=f'{SC}/t6_blocked.png', full_page=True)
        await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(500)
        await pg.click('#blockOpen'); await pg.wait_for_timeout(500)
        assert '차단한 사용자' in await pg.locator('.sheet').inner_text()
        await pg.click('[data-unblock]'); await pg.wait_for_timeout(500)
        assert await pg.evaluate('S.blocked.length') == 0, '차단 해제가 안 된다'
        await pg.click('#sheetClose'); await pg.wait_for_timeout(300)

        # 원장은 어느 글이든 삭제할 수 있다
        await login(pg, 'owner')
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        n0 = await pg.locator('.pcard').count()
        await pg.click('.pcard'); await pg.wait_for_timeout(500)
        assert await pg.locator('#pDel').count() == 1, '원장 삭제 버튼이 없다'
        await pg.click('#pDel'); await pg.wait_for_timeout(700)
        assert await pg.locator('.pcard').count() == n0 - 1, '삭제되지 않았다'
        assert not errs, errs
        print('TALK OK', errs); await b.close()
async def server_mode():

    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx=await b.new_context(viewport={'width':390,'height':844}); pg=await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(APP); await pg.wait_for_timeout(800)
        await pg.click('#goSignup'); await pg.wait_for_timeout(400)
        await pg.fill('#suName','서버학생'); await pg.fill('#suEmail','s1@demo.kr'); await pg.fill('#suPw','123456')
        await pg.check('#suAgree'); await pg.click('#suGo'); await pg.wait_for_timeout(1200)
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(600)
        await pg.click('#postNew'); await pg.wait_for_timeout(400)
        await pg.fill('#nkIn','서버닉'); await pg.click('#nkSave'); await pg.wait_for_timeout(900)
        assert await pg.evaluate('ACC && ACC.nick') == '서버닉', await pg.evaluate('ACC && ACC.nick')
        await pg.fill('#poT','서버 모드에서 글이 올라가나요')
        await pg.fill('#poX','모의 Supabase 앞에서 글쓰기·댓글·도움됨·채택이 도는지 확인합니다.')
        await pg.click('#poSave'); await pg.wait_for_timeout(1100)
        assert await pg.locator('.pcard').count() == 1
        await pg.click('.pcard'); await pg.wait_for_timeout(800)
        await pg.fill('#cIn','댓글도 됩니다.'); await pg.click('#cGo'); await pg.wait_for_timeout(1000)
        assert await pg.locator('.cm').count() == 1, '댓글 실패'
        await pg.click('#pLike'); await pg.wait_for_timeout(800)
        assert '1' in await pg.locator('#pLike').inner_text()
        await pg.click('[data-cpick]'); await pg.wait_for_timeout(900)
        assert await pg.locator('.cm .picked').count() == 1, '채택 실패'
        await pg.click('#talkBack'); await pg.wait_for_timeout(800)
        assert await pg.locator('.pcard .ok').count() == 1, '해결됨 표시 실패'
        # 연결이 끊겼을 때 빈 화면 대신 안내가 뜨는가
        await ctx.route(lambda url: '8766' in url, lambda r: asyncio.ensure_future(r.abort()))
        await pg.click('.tab[data-v="plan"]'); await pg.wait_for_timeout(500)
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(1200)
        assert await pg.locator('.loadfail').count() == 1, '불러오기 실패 안내가 없다'
        assert await pg.locator('.netbar').count() == 1, '연결 안내 띠가 없다'
        await ctx.set_offline(True); await pg.evaluate("window.dispatchEvent(new Event('offline'))"); await pg.wait_for_timeout(400)
        assert '인터넷에 연결되어 있지 않습니다' in await pg.locator('.netbar span').inner_text()
        await ctx.set_offline(False); await ctx.unroute_all()
        await pg.evaluate("window.dispatchEvent(new Event('online'))"); await pg.wait_for_timeout(300)
        await pg.click('#talkRetry'); await pg.wait_for_timeout(900)
        assert await pg.locator('.loadfail').count() == 0, '다시 불러오기가 듣지 않는다'
        assert await pg.locator('.netbar').count() == 0, '복구 뒤에도 안내 띠가 남는다'

        assert not errs, errs
        print('SERVER TALK OK'); await b.close()

asyncio.run(server_mode() if '--server' in sys.argv else main())
