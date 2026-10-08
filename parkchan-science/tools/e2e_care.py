#!/usr/bin/env python3
"""이야기 안전장치 E2E — 힘든 마음(자해·자살 신호)이 담긴 글·댓글.

· 올리기 전에 상담 창구(109·1388) 창이 뜨고, '잠시 쉬었다'면 올리지 않는다 · '글 올리기'면 그대로 올린다(막지 않는다)
· 글 아래 조용한 안내(쓴 사람/읽는 사람 문구가 다름) · 과학 용어('세포 자살')·'유서 깊은'·'배고파 죽겠다'는 걸리지 않는다
· 원장 화면 '먼저 살펴볼 글'에 이름·학원 코드와 함께 뜬다(학생은 이 목록을 못 받는다)
· 내 정보 '마음이 힘들 때' — 언제든 상담 창구

전제: docs/parkchan :8765, --server 면 시험대 :8767.   사용: python3 tools/e2e_care.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes, member
SERVER = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon'] if SERVER else ''
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}' if SERVER else 'http://127.0.0.1:8765/index.html?server='
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_care'; os.makedirs(SC, exist_ok=True)
OWNER_PW = 'owner-pass' if SERVER else '2580'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        if SERVER: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
        async def page(dark=False):
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}, color_scheme='dark' if dark else 'light'); await ctx.add_init_script(NO_INTRO); pg = await ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await pg.goto(APP); await pg.wait_for_timeout(500); return ctx, pg
        async def write_post(pg, title, body):
            await pg.click('.tab[data-v="talk"]'); await pg.wait_for_timeout(400)
            await pg.click('#postNew'); await pg.wait_for_timeout(300)
            if await pg.locator('#nkIn').count():
                await pg.fill('#nkIn', '마음' + str(len(title))); await pg.click('#nkSave'); await pg.wait_for_timeout(600)
            await pg.select_option('#poB', 'talk'); await pg.fill('#poT', title); await pg.fill('#poX', body); await pg.click('#poSave'); await pg.wait_for_timeout(500)

        # ① 학생 A — 힘든 마음을 담은 글
        c1, s = await page()
        await signup(s, '마음학생', 'care@t.kr'); await s.wait_for_timeout(600); await member(s)
        await write_post(s, '요즘 너무 지쳐요', '공부도 안 되고 다 그만 살고 싶다는 생각이 들어요')
        assert await s.locator('#careH').count() == 1, '상담 창구 창이 안 뜸'
        txt = await s.inner_text('.sheet.care'); assert '109' in txt and '1388' in txt and '112' in txt, txt
        assert '밤이나 주말엔 바로 못 볼 수 있어요' in txt and '24시간' in txt, ('밤·주말 안내 한 줄', txt)
        assert await s.locator('.sheet.care a[href="tel:109"]').count() == 1 and await s.locator('.sheet.care a[href="tel:1388"]').count() == 1
        assert await s.evaluate('document.activeElement.id') == 'careWait', '초점은 "잠시 쉬었다"에'
        await s.screenshot(path=f'{SC}/c01_care_sheet.png')
        await s.click('#careWait'); await s.wait_for_timeout(300)
        assert await s.locator('#poT').count() == 1, '잠시 쉬기를 골랐는데 쓰던 글이 사라짐'
        assert await s.evaluate('DBX.posts("전체","").then(l => l.length)') == 0, '잠시 쉬기를 골랐는데 올라감'
        await s.click('#poSave'); await s.wait_for_timeout(300); await s.click('#carePost'); await s.wait_for_timeout(700)
        assert await s.evaluate('view') == 'talk'
        await s.click('.pcard'); await s.wait_for_timeout(500)
        assert await s.locator('.carenote').count() == 1 and '고마워요' in await s.inner_text('.carenote'), '쓴 사람에게 안내 줄이 없음'
        await s.click('#openHelp'); await s.wait_for_timeout(250); assert await s.locator('.sheet .help .hc').count() == 2; await s.click('#sheetClose')
        await s.screenshot(path=f'{SC}/c02_post_author.png', full_page=True)

        # ② 걸리지 않아야 할 말: 과학 용어·관용구
        await write_post(s, '세포 자살 질문', '아폽토시스를 세포 자살이라고 하나요? 유서 깊은 실험이라던데, 배고파 죽겠다 ㅋㅋ')
        assert await s.locator('#careH').count() == 0, '과학 용어·관용구에 상담 창이 뜸(오탐)'
        assert await s.evaluate('view') == 'talk'
        # ②-2 청소년 은어(docs/11 §12-4)는 걸리고, 비슷한 보통 말은 걸리지 않는다
        await write_post(s, '진짜 힘들다', '시험 망해서 그냥 뒤지고 싶다')
        assert await s.locator('#careH').count() == 1, "은어 '뒤지고 싶'에 상담 창이 안 뜸"
        await s.click('#careWait'); await s.wait_for_timeout(200); await s.click('#sheetClose'); await s.wait_for_timeout(200)
        await write_post(s, '서랍 정리', '서랍을 뒤져 보니 작년 노트가 나왔어요. 숙제가 많아 죽겠다 ㅠ')
        assert await s.locator('#careH').count() == 0, "'뒤져 보니'·'죽겠다'에 상담 창이 뜸(오탐)"
        assert await s.evaluate('view') == 'talk'

        # ③ 학생 B — 읽는 사람 문구 · 댓글에도 같은 안전장치 (같은 창에서 계정 바꾸기 — 로컬 모드는 창마다 저장소가 따로라)
        async def logout(pg):
            await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await auto_yes(pg); await pg.click('#logout'); await pg.wait_for_timeout(700)
        await logout(s); s2 = s; await s2.emulate_media(color_scheme='dark')
        await signup(s2, '친구학생', 'friend@t.kr'); await s2.wait_for_timeout(600); await member(s2)
        await s2.evaluate("DBX.setNick('친구').then(a => ACC = a)"); await s2.wait_for_timeout(400)
        await s2.click('.tab[data-v="talk"]'); await s2.wait_for_timeout(500)
        await s2.locator('.pcard', has_text='요즘 너무 지쳐요').click(); await s2.wait_for_timeout(500)
        assert '따뜻한 말' in await s2.inner_text('.carenote'), '읽는 사람 안내 문구가 다름'
        assert '방법·장소는 묻지도 적지도 말아요' in await s2.inner_text('.carehint'), '위기 글 댓글 칸 위 한 줄이 없음'
        await s2.evaluate("DBX.setNick('친구').then(a => ACC = a)"); await s2.wait_for_timeout(400)
        await s2.fill('#cIn', '나도 그런 날 있어. 같이 버티자. 나도 가끔 자해하고 싶었어'); await s2.click('#cGo'); await s2.wait_for_timeout(400)
        assert await s2.locator('#careH').count() == 1, '댓글에도 상담 창이 떠야 함'
        await s2.click('#carePost'); await s2.wait_for_timeout(700)
        assert await s2.locator('.cm').count() >= 1
        await s2.screenshot(path=f'{SC}/c03_reader_dark.png', full_page=True)
        # ③-2 '친구가 걱정돼요' — 가입 첫날에도 · 1건이어도 원장에게 · 글은 가리지 않음 · 알려 준 학생에게 109·1388
        await s2.click('#pReport'); await s2.wait_for_timeout(300); await s2.click('[data-rsn="worry"]'); await s2.click('#rpGo'); await s2.wait_for_timeout(800)
        assert '알려 줘서 고마워요' in await s2.inner_text('.sheet h3'), '걱정돼요 뒤 안내 창이 없음'
        assert await s2.locator('.sheet a[href="tel:109"]').count() == 1 and await s2.locator('.sheet a[href="tel:1388"]').count() == 1
        await s2.screenshot(path=f'{SC}/c03b_worry_sheet.png'); await s2.click('#sheetClose'); await s2.wait_for_timeout(500)
        assert '요즘 너무 지쳐요' in await s2.inner_text('.pfull h2'), '걱정돼요 신고로 글이 가려짐'
        assert await s2.evaluate('DBX.post(postId).then(x => x.report_n)') == 0, '걱정돼요가 가림 수에 들어감'
        if SERVER:   # 학생은 원장 목록을 못 받는다
            assert await s2.evaluate('DBX.careList()') == [], '학생이 먼저 살펴볼 글 목록을 받음'

        # ④ 원장 — 먼저 살펴볼 글(글 1 + 댓글 1), 이름까지
        await s2.emulate_media(color_scheme='light'); await logout(s2); o = s
        await o.click('#goLogin'); await o.fill('#lgEmail', 'owner@parkchan.kr'); await o.fill('#lgPw', OWNER_PW); await o.click('#lgGo'); await o.wait_for_timeout(900)
        await o.click('[data-adm="talk"]'); await o.wait_for_timeout(700)
        box = o.locator('.carerow'); assert await box.count() == 1, '원장 화면에 먼저 살펴볼 글이 없음'
        t = await box.inner_text(); assert '2건' in t and '마음학생' in t and '친구학생' in t and '세포 자살' not in t, t
        assert '친구가 걱정돼요 1' in t and await box.locator('[data-admcdone]').count() == 1, ('걱정돼요 표시', t)
        await o.screenshot(path=f'{SC}/c04_owner.png', full_page=True)
        await box.locator('[data-admcdone]').click(); await o.wait_for_timeout(800)
        assert '친구가 걱정돼요' not in await o.locator('.carerow').inner_text(), '살펴봤어요 뒤에도 걱정돼요 표시가 남음'
        await box.locator('[data-admcare]').first.click(); await o.wait_for_timeout(500); assert await o.evaluate('view') == 'post'

        # ④-2 알려 준 친구에게 결과(원장님이 살펴봤어요)
        await logout(o); await s.click('#goLogin'); await s.fill('#lgEmail', 'friend@t.kr'); await s.fill('#lgPw', 'pass1234'); await s.click('#lgGo'); await s.wait_for_timeout(900)
        await s.click('.tab[data-v="talk"]'); await s.wait_for_timeout(800)
        assert '걱정된다고 알려 준 글을 살펴봤어요' in await s.inner_text('.repdone'), '걱정돼요 결과가 알려 준 학생에게 안 감'
        await s.screenshot(path=f'{SC}/c04b_friend_result.png'); await s.click('#repSeen'); await s.wait_for_timeout(600)
        # ⑤ 내 정보 — 마음이 힘들 때 (학생으로 다시)
        await logout(s); await s.click('#goLogin'); await s.fill('#lgEmail', 'care@t.kr'); await s.fill('#lgPw', 'pass1234'); await s.click('#lgGo'); await s.wait_for_timeout(900)
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#goHelp'); await s.wait_for_timeout(250)
        assert await s.locator('.sheet .help a[href="tel:109"]').count() == 1
        await s.screenshot(path=f'{SC}/c05_help_sheet.png')
        assert not errs, errs
        print(f'CARE E2E OK ({"server" if SERVER else "local"}) · 콘솔 오류', errs); await b.close()

asyncio.run(main())
