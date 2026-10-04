#!/usr/bin/env python3
"""이야기(커뮤니티) E2E — 닉네임 · 글쓰기 · 개념 첨부 · 댓글 · 채택 · 도움됨 · 신고/가림 · 개인정보 감지 · 원장 삭제.
사전: docs/parkchan 을 http://127.0.0.1:8765 로 띄운 뒤  python3 tools/e2e_talk.py --shots DIR
서버 모드도 확인하려면 tools/testbed_up.sh 로 시험대(:8767)를 띄우고  --server 를 덧붙인다.
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes, member
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/pcs-e2e-talk'
os.makedirs(SC, exist_ok=True)
import json as _j, urllib.request as _u
GW = 'http://127.0.0.1:8767'   # tools/testbed_up.sh — 진짜 Postgres·PostgREST 시험대
try: ANON = _j.loads(_u.urlopen(GW + '/__anon').read())['anon']
except Exception: ANON = 'anon'
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'

async def login(pg, who):
    await pg.evaluate("['pcs.v2','pcs.local.sid','pcs.session'].forEach(k=>localStorage.removeItem(k))")
    await pg.goto('http://127.0.0.1:8765/index.html'); await pg.wait_for_timeout(700)
    await pg.click('#goLogin'); await pg.click(f'[data-demo^="{who}"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(900)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg)
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
        await signup(pg, '김학생', 'b@demo.kr')
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        # 학원 코드·이용권이 없는 학생 계정은 읽기만(2026-10 · docs/11 §12-9) — 글쓰기 단추 대신 조용한 안내
        assert await pg.locator('#postNew').count() == 0 and '학원 코드나 이용권' in await pg.inner_text('#talkGate'), '손님 계정에 글쓰기가 열려 있다'
        await pg.click('.pcard'); await pg.wait_for_timeout(500)
        assert await pg.locator('#cIn').count() == 0 and await pg.locator('#cGate').count() == 1, '손님 계정에 댓글 칸이 있다'
        await pg.screenshot(path=f'{SC}/t3b_member_gate.png', full_page=True)
        await pg.click('#talkBack'); await pg.wait_for_timeout(400)
        await member(pg); await pg.click('.tab[data-v="today"]'); await pg.wait_for_timeout(300); await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(500)
        assert await pg.locator('#postNew').count() == 1, '이용권을 넣었는데 글쓰기가 안 열림'
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
        ctx=await b.new_context(viewport={'width':390,'height':844}); await ctx.add_init_script(NO_INTRO); pg=await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(pg)
        _u.urlopen(_u.Request(GW + '/__reset', method='POST')).read()
        await pg.goto(APP); await pg.wait_for_timeout(800)
        await signup(pg, '서버학생', 's1@demo.kr'); await member(pg)
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
        await ctx.route(lambda url: '8767' in url, lambda r: asyncio.ensure_future(r.abort()))
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
        # 원장이 답을 달면: 선생님 표시 · 글쓴이에게 새 댓글 표시(탭 점 → 글을 열면 사라짐)
        oc = await b.new_context(viewport={'width':390,'height':844}); await oc.add_init_script(NO_INTRO); o = await oc.new_page(); o.on('pageerror', lambda e: errs.append(str(e)))
        await o.goto(APP); await o.wait_for_timeout(600)
        await o.click('#goLogin'); await o.fill('#lgEmail','owner@parkchan.kr'); await o.fill('#lgPw','owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(1000)
        await o.click('.tab[data-v="talk"]'); await o.wait_for_timeout(700); await o.click('.pcard'); await o.wait_for_timeout(800)
        await o.fill('#cIn','그래프 넓이 = 힘 × 시간 = 충격량입니다.'); await o.click('#cGo'); await o.wait_for_timeout(900)
        assert await o.locator('.cm.staffc .staff').count() == 1, '원장 댓글에 선생님 표시가 없다'
        await pg.reload(); await pg.wait_for_timeout(2200)
        assert await pg.locator('.tab[data-v="talk"] .tdot').count() == 1, '새 댓글 점이 안 뜬다'
        await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(800)
        assert '새 댓글 1' in await pg.locator('.pcard .newc').first.inner_text()
        await pg.screenshot(path=f'{SC}/t_srv_newc.png')
        await pg.click('.pcard'); await pg.wait_for_timeout(900)
        assert await pg.locator('.cm .staff').count() == 1 and '원장님' in await pg.locator('.cm.staffc b').inner_text()
        assert await pg.locator('.tab .tdot').count() == 0, '글을 열었는데 탭 점이 남는다'
        await pg.screenshot(path=f'{SC}/t_srv_staff.png', full_page=True)
        await pg.click('#talkBack'); await pg.wait_for_timeout(800)
        assert await pg.locator('.pcard .newc').count() == 0 and await pg.locator('.tab .tdot').count() == 0, '읽었는데 새 댓글 표시가 남는다'
        await oc.close()

        assert not errs, errs
        print('SERVER TALK OK'); await b.close()

async def server_safety():
    """2026-10 docs/11 §12 — 신고 사유 · 이용 제한(원장 → 학생, 서버가 막음) · 이의 제기 · 신고 결과 알림 · 되돌린 신고 재신고 · 전화번호 가림 · 학교+학년+이름 · 보호자 읽기 전용"""
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        async def page():
            c = await b.new_context(viewport={'width': 390, 'height': 844}); await c.add_init_script(NO_INTRO); pg = await c.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e))); await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700); return c, pg
        async def nick(pg, n):
            await pg.evaluate(f"DBX.setNick('{n}').then(a => ACC = a)"); await pg.wait_for_timeout(300)
        async def talk(pg):
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(200); await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(800)
        _u.urlopen(_u.Request(GW + '/__reset', method='POST')).read()
        # 학생 A — 닉네임 금지어(앱과 서버가 같은 목록) · 전화번호는 가려서 올라감 · 학교+학년+이름 경고
        ca, a = await page(); await signup(a, '가학생', 'ra@demo.kr'); await member(a)
        await talk(a); await a.click('#postNew'); await a.wait_for_timeout(300)
        await a.fill('#nkIn', '과학 쌤'); await a.click('#nkSave'); await a.wait_for_timeout(300)
        assert '선생님·원장' in await a.inner_text('#nkWarn'), "앱이 '쌤'(띄어쓰기) 닉네임을 통과시킴"
        s_, j = await a.evaluate("DBX.setNick('수학.쌤').then(() => [0, ''], e => [1, e.message])")
        assert s_ == 1 and '선생님' in j, ('서버도 같은 금지어', j)
        await a.fill('#nkIn', '물리하는가'); await a.click('#nkSave'); await a.wait_for_timeout(600)
        await a.fill('#poT', '운동량 질문 있어요'); await a.fill('#poX', '충격량 단원 질문입니다. 답 주실 분은 010-1234-5678 로 문자 주세요')
        await a.click('#poSave'); await a.wait_for_timeout(300)
        w = await a.inner_text('#poWarn'); assert '전화번호로' in w and '010-****-5678' in w, w
        await a.screenshot(path=f'{SC}/s1_phone_warn.png')
        await a.click('#poSave'); await a.wait_for_timeout(900); await a.click('.pcard'); await a.wait_for_timeout(700)
        body = await a.inner_text('.pfull .body'); assert '010-****-5678' in body and '1234' not in body, ('서버가 가운데를 가려 저장', body)
        await a.fill('#cIn', '저는 한빛중 3학년 김민수예요 같이 공부해요'); await a.click('#cGo'); await a.wait_for_timeout(500)
        assert '학교·학년과 이름으로' in await a.inner_text('.piiwarn'), '학교+학년+이름 경고가 없음'
        await a.fill('#cIn', '(댓글 고침) 같이 공부해요'); await a.click('#cGo'); await a.wait_for_timeout(700)
        a_uid = await a.evaluate('ACC.id')
        # 학생 B — 사유를 골라 신고
        cb, bb = await page(); await signup(bb, '나학생', 'rb@demo.kr'); await member(bb, aged=True); await nick(bb, '신고하는나')
        await talk(bb); await bb.click('.pcard'); await bb.wait_for_timeout(700); await bb.click('#pReport'); await bb.wait_for_timeout(300)
        assert await bb.locator('.rsn [data-rsn]').count() == 7 and await bb.locator('[data-rsn="worry"]').count() == 1, '신고 사유가 7개(걱정돼요 포함)가 아님'
        assert await bb.is_disabled('#rpGo'), '사유를 고르기 전에 신고 단추가 눌림'
        await bb.click('[data-rsn="bully"]'); await bb.screenshot(path=f'{SC}/s2_report_reasons.png')
        await bb.click('#rpGo'); await bb.wait_for_timeout(700)
        n = await bb.evaluate(f"DBX.post('{await bb.evaluate('postId')}').then(x => x.report_n)"); assert n == 1, n
        # 원장 — 사유별 건수 · 글에서 '차단' 대신 '이용 제한' · 7일
        co, o = await page(); await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(1000)
        await o.click('[data-adm="talk"]'); await o.wait_for_timeout(900)
        assert '괴롭힘 1' in await o.inner_text('#v-admin'), '원장 목록에 신고 사유가 없음'
        await o.click('.tab[data-v="talk"]'); await o.wait_for_timeout(700); await o.click('.pcard'); await o.wait_for_timeout(700)
        assert await o.locator('#pBlock').count() == 0 and await o.locator('#pLimit').count() == 1, '원장 글 화면에 차단(제재 아님)이 남음'
        await o.click('#pLimit'); await o.wait_for_timeout(500)
        assert await o.get_attribute('[data-lmd="7"]', 'aria-checked') == 'true', '처음 제한은 7일이 골라져 있어야 함'
        await o.select_option('#lmR', '친구를 놀리거나 괴롭혔어요'); await o.fill('#lmM', '비방 댓글 · 통화함')
        await o.screenshot(path=f'{SC}/s3_limit_sheet.png'); await o.click('#lmGo'); await o.wait_for_timeout(900)
        # 학생 A — 차분한 안내 · 쓰기는 서버가 막음 · 이의 제기
        await a.reload(); await a.wait_for_timeout(1500); await talk(a)
        g = await a.inner_text('#talkGate'); assert '쉬는 중이에요' in g and '괴롭혔어요' in g and '다시 살펴봐' in g, g
        assert await a.locator('#postNew').count() == 0
        await a.screenshot(path=f'{SC}/s4_limited_student.png')
        r = await a.evaluate("DBX.addPost({ board:'talk', title:'우회', body:'앱을 거치지 않고 올리기' }).then(() => 'ok', e => e.message)")
        assert '쉬는 중' in r, ('제한 중 글쓰기를 서버가 막아야 함', r)
        r = await a.evaluate(f"DBX.addComment(postId || '00000000-0000-0000-0000-000000000000', '댓글 우회').then(() => 'ok', e => e.message)")
        assert r != 'ok', ('제한 중 댓글을 서버가 막아야 함', r)
        await a.click('#talkAppeal'); await a.wait_for_timeout(400); assert '다시 살펴봐 주세요' in await a.inner_text('.sheet h3')
        await a.fill('#fbBody', '장난으로 쓴 말이었는데 친구에게 사과했어요. 다시 봐 주세요.'); await a.click('#fbSend'); await a.wait_for_timeout(800)
        fb = await o.evaluate("DBX.feedbackList()"); assert any(x.get('ref') == 'talk:appeal' for x in fb), fb
        # 원장 — 신고 되돌리기 → 신고한 학생에게 결과 · 같은 학생 재신고는 다시 세지 않음
        await o.click('.tab[data-v="admin"]'); await o.wait_for_timeout(500); await o.click('[data-adm="talk"]'); await o.wait_for_timeout(900)
        assert '이야기 이용 제한 1명' in await o.inner_text('#limSec'), await o.inner_text('#limSec')
        await o.screenshot(path=f'{SC}/s5_admin_talk.png', full_page=True)
        await o.click('[data-admclr^="post:"]'); await o.wait_for_timeout(900)
        await talk(bb); assert '그대로 두었어요 1건' in await bb.inner_text('.repdone'), '신고한 학생에게 결과가 안 감'
        await bb.screenshot(path=f'{SC}/s6_report_result.png')
        await bb.click('#repSeen'); await bb.wait_for_timeout(700); assert await bb.locator('.repdone').count() == 0, '확인한 결과가 또 뜸'
        pid = await bb.evaluate("DBX.posts('전체','').then(l => l.find(x => x.title.startsWith('운동량')).id)")
        r = await bb.evaluate(f"DBX.reportItem('post', '{pid}', 'bully')"); assert r.get('again') and r.get('checked'), r
        n = await bb.evaluate(f"DBX.post('{pid}').then(x => x.report_n)"); assert n == 0, ('되돌린 뒤 같은 학생 재신고로 다시 셈', n)
        # 원장 — 풀기 → 다시 쓸 수 있음
        await o.click('[data-admlift]'); await o.wait_for_timeout(900); assert '0명' in await o.inner_text('#limSec')
        await talk(a); assert await a.locator('#postNew').count() == 1, '제한을 풀었는데 글쓰기가 안 열림'
        # 보호자 — 읽기만(서버도 막음)
        cp, pp = await page(); await signup(pp, '다보호자', 'rp@demo.kr', role='parent'); await talk(pp)
        assert '보호자 계정은 읽기만' in await pp.inner_text('#talkGate') and await pp.locator('#postNew').count() == 0
        await pp.screenshot(path=f'{SC}/s7_parent_gate.png')
        r = await pp.evaluate("DBX.addPost({ board:'talk', title:'보호자 글', body:'보호자가 올려 봅니다' }).then(() => 'ok', e => e.message)"); assert '보호자' in r, r
        await pp.click('.pcard'); await pp.wait_for_timeout(700); assert await pp.locator('#cIn').count() == 0, '보호자에게 댓글 칸'
        assert not errs, errs
        print('SERVER TALK SAFETY OK'); await b.close()

async def server_review():
    """2026-10 docs/11 §12-6·7·11·14 — 첫 글 검토(검토 중 → 공개 안 함 → 고쳐 다시 → 공개) · 선생님 확인(맨 위·초록 체크) ·
    답이 없는 질문(48시간) · 처리 기록 · 욕설 미리 경고(한 번 더 묻기 · 아주 심한 욕은 막음)"""
    keys = _j.loads(_u.urlopen(GW + '/__anon').read()); SVC = keys['service']
    def svc(path, body, m='PATCH'):
        _u.urlopen(_u.Request(GW + '/rest/v1/' + path, data=_j.dumps(body).encode(), method=m, headers={'Content-Type': 'application/json', 'apikey': SVC, 'Authorization': 'Bearer ' + SVC})).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        async def page():
            c = await b.new_context(viewport={'width': 390, 'height': 844}); await c.add_init_script(NO_INTRO); pg = await c.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e))); await auto_yes(pg); await pg.goto(APP); await pg.wait_for_timeout(700); return c, pg
        async def talk(pg):
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(200); await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(800)
        _u.urlopen(_u.Request(GW + '/__reset', method='POST')).read()
        # 새 학생 N — 첫 글은 '검토 중'(쓴 사람만 봄)
        cn, n = await page(); await signup(n, '새로온학생', 'rv1@demo.kr'); await member(n, trust=False)
        await talk(n); await n.click('#postNew'); await n.wait_for_timeout(300)
        await n.fill('#nkIn', '병신같은닉'); await n.click('#nkSave'); await n.wait_for_timeout(300)
        assert '욕설' in await n.inner_text('#nkWarn'), '앱이 욕설 닉네임을 통과시킴'
        await n.fill('#nkIn', '새싹과학'); await n.click('#nkSave'); await n.wait_for_timeout(700)
        assert await n.locator('#poFirst').count() == 1, '첫 글 안내 한 줄이 없음'
        await n.fill('#poT', '광합성 질문이요'); await n.fill('#poX', '빛 반응이 어디서 일어나는지 헷갈려요. 틸라코이드 맞나요?')
        await n.screenshot(path=f'{SC}/r0_first_sheet.png'); await n.click('#poSave'); await n.wait_for_timeout(1000)
        assert await n.locator('.pcard .rvw').count() == 1 and '검토 중' in await n.inner_text('.pcard .rvw'), '내 글에 검토 중 표시가 없음'
        await n.screenshot(path=f'{SC}/r1_pending_list.png')
        await n.click('.pcard'); await n.wait_for_timeout(700); assert '원장님이 확인하고 있어요' in await n.inner_text('#rvNote')
        await n.screenshot(path=f'{SC}/r2_pending_post.png', full_page=True)
        pid = await n.evaluate('postId')
        # 다른 학생 B — 안 보임 · 욕설 미리 경고
        cb, bb = await page(); await signup(bb, '헌학생', 'rv2@demo.kr'); await member(bb); await bb.evaluate("DBX.setNick('오래된친구').then(a => ACC = a)"); await bb.wait_for_timeout(300)
        await talk(bb); assert await bb.locator('.pcard').count() == 0, '검토 중인 첫 글이 다른 학생에게 보임'
        await bb.click('#postNew'); await bb.wait_for_timeout(300)
        await bb.fill('#poT', '시험 망함'); await bb.fill('#poX', '아 진짜 씨발 이번 시험 망했다 다들 어땠어')
        await bb.evaluate('window.__askManual = true'); await bb.click('#poSave'); await bb.wait_for_timeout(400)
        assert '상처가 될 수 있어요' in await bb.inner_text('#askMsg') and await bb.inner_text('#askNo') == '고쳐 쓸게요', '욕설 경고가 안 뜸'
        await bb.screenshot(path=f'{SC}/r3_abuse_ask.png'); await bb.click('#askNo'); await bb.wait_for_timeout(300)
        assert await bb.locator('#poT').count() == 1, '고쳐 쓸게요를 눌렀는데 창이 닫힘'
        await bb.fill('#poX', '느 금 마 진짜'); await bb.click('#poSave'); await bb.wait_for_timeout(400)
        assert '아주 심한 욕설' in await bb.inner_text('#poWarn'), '아주 심한 욕을 앱이 막지 않음'
        r = await bb.evaluate("DBX.addPost({ board:'talk', title:'우회', body:'니애미' }).then(() => 'ok', e => e.message)"); assert '심한 욕설' in r, ('서버도 거절', r)
        await bb.fill('#poX', '이번 시험 망했다 다들 어땠어'); await bb.click('#poSave'); await bb.wait_for_timeout(900)
        await bb.evaluate('window.__askManual = false')
        # 원장 — 맨 위 '검토할 첫 글' · 공개 안 함(사유)
        co, o = await page(); await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', 'owner-pass'); await o.click('#lgGo'); await o.wait_for_timeout(1000)
        await o.click('[data-adm="talk"]'); await o.wait_for_timeout(900)
        first_sec = await o.evaluate("document.querySelector('#v-admin .sec')?.id")
        assert first_sec == 'rvSec' and '검토할 첫 글 1건' in await o.inner_text('#rvSec') and '새로온학생' in await o.inner_text('#rvSec'), (first_sec, await o.inner_text('#v-admin'))
        await o.screenshot(path=f'{SC}/r4_owner_review.png', full_page=True)
        await o.click('[data-rvno]'); await o.wait_for_timeout(400); await o.select_option('#rjR', '이야기 규칙에 맞지 않아요'); await o.fill('#rjF', '제목을 조금 더 구체적으로 적어 주세요')
        await o.screenshot(path=f'{SC}/r5_reject_sheet.png'); await o.click('#rjGo'); await o.wait_for_timeout(900)
        assert await o.locator('#rvSec').count() == 0, '처리했는데 검토 목록이 남음'
        await n.reload(); await n.wait_for_timeout(1300); await talk(n); assert '공개 안 됨' in await n.locator('.pcard', has_text='광합성').locator('.rvw').inner_text()
        await n.locator('.pcard', has_text='광합성').click(); await n.wait_for_timeout(700); t = await n.inner_text('#rvNote'); assert '공개하지 않았어요' in t and '구체적으로' in t, t
        await n.screenshot(path=f'{SC}/r6_rejected_author.png', full_page=True)
        await n.click('#pEdit'); await n.wait_for_timeout(400); await n.fill('#poT', '광합성 빛 반응이 일어나는 장소 질문'); await n.click('#poSave'); await n.wait_for_timeout(900)
        assert '원장님이 확인하고 있어요' in await n.inner_text('#rvNote'), '고쳐 쓰면 다시 검토 중이어야 함'
        # 원장 — 글 화면에서 공개 → B 에게 보임 · N 의 다음 글은 바로
        await o.click('.tab[data-v="talk"]'); await o.wait_for_timeout(700); await o.locator('.pcard', has_text='광합성').click(); await o.wait_for_timeout(700)
        await o.click('#pRvOk'); await o.wait_for_timeout(900); assert await o.locator('#rvNote').count() == 0
        await talk(bb); assert await bb.locator('.pcard', has_text='광합성').count() == 1, '공개했는데 다른 학생에게 안 보임'
        await talk(n); await n.click('#postNew'); await n.wait_for_timeout(300); assert await n.locator('#poFirst').count() == 0, '공개 뒤에도 첫 글 안내가 남음'
        await n.fill('#poT', '두 번째 질문'); await n.fill('#poX', '이번엔 바로 올라가나요? 궁금합니다'); await n.click('#poSave'); await n.wait_for_timeout(900)
        await talk(bb); assert await bb.locator('.pcard', has_text='두 번째 질문').count() == 1, '공개 뒤 새 글이 바로 안 보임'
        # 선생님 확인 — 학생 답 둘 중 늦게 단 것을 확인하면 맨 위 · 초록 체크
        await bb.locator('.pcard', has_text='광합성').click(); await bb.wait_for_timeout(700)
        await bb.fill('#cIn', '엽록체 바깥쪽 막에서 일어나요'); await bb.click('#cGo'); await bb.wait_for_timeout(800)
        await bb.fill('#cIn', '틸라코이드 막에서 일어나요. 스트로마는 탄소 고정!'); await bb.click('#cGo'); await bb.wait_for_timeout(800)
        await o.click('#talkBack'); await o.wait_for_timeout(600); await o.locator('.pcard', has_text='광합성').click(); await o.wait_for_timeout(700)
        await o.locator('.cm', has_text='틸라코이드 막에서').locator('[data-cchk]').click(); await o.wait_for_timeout(900)
        await bb.reload(); await bb.wait_for_timeout(1300); await talk(bb); await bb.locator('.pcard', has_text='광합성').click(); await bb.wait_for_timeout(800)
        first = bb.locator('.cm').first; assert '틸라코이드 막에서' in await first.inner_text() and await first.locator('.chk').count() == 1, '선생님 확인 답이 맨 위·체크가 아님'
        await bb.screenshot(path=f'{SC}/r7_checked.png', full_page=True)
        # 답이 없는 질문(48시간) — 질문을 사흘 전으로 돌린다
        qid = await bb.evaluate("DBX.addPost({ board:'qna', title:'아무도 안 답한 질문', body:'산화 환원 질문입니다' }).then(x => x.id)")
        import datetime as _d; svc(f'posts?id=eq.{qid}', {'at': (_d.datetime.now(_d.timezone.utc) - _d.timedelta(days=3)).isoformat()})
        await o.click('.tab[data-v="admin"]'); await o.wait_for_timeout(500); await o.click('[data-adm="talk"]'); await o.wait_for_timeout(900)
        u = await o.inner_text('#unaBox'); assert '아무도 안 답한 질문' in u and '광합성' not in u, u
        await o.click('#logBox summary'); await o.wait_for_timeout(200)
        lg = await o.inner_text('#logBox'); assert all(w in lg for w in ('첫 글 공개', '첫 글 공개 안 함', '선생님 확인', '원장')), lg
        await o.screenshot(path=f'{SC}/r8_owner_log.png', full_page=True)
        await o.click('#unaBox [data-admcare]'); await o.wait_for_timeout(700); assert await o.evaluate('view') == 'post'
        await o.fill('#cIn', '산화는 전자를 잃는 것입니다.'); await o.click('#cGo'); await o.wait_for_timeout(800)
        await o.click('.tab[data-v="admin"]'); await o.wait_for_timeout(700)
        assert '아무도 안 답한 질문' not in await o.inner_text('#unaBox'), '선생님이 답했는데 답 없는 질문에 남음'
        assert not errs, errs
        print('SERVER TALK REVIEW OK'); await b.close()

if '--server' in sys.argv:
    asyncio.run(server_mode()); asyncio.run(server_safety()); asyncio.run(server_review())
else: asyncio.run(main())
