#!/usr/bin/env python3
"""의견 보내기 · 교재 오류 신고 E2E — 학생이 개념·문제에서 '틀린 곳'을 알리면 어디서 보냈는지가 같이 가고,
원장님은 학생 탭 '받은 의견'에서 이름·개념과 함께 보고 '개념 보기'로 바로 가서 '처리함'을 누른다.

· 비로그인은 로그인 안내 · 빈 글·주민등록번호는 막음 · 종류 고르기 · 글자 수 · 힘든 마음이 담긴 의견은 상담 창구 안내 + 원장에게 '먼저 살펴보기'
· 로컬(시연) 모드와 서버 모드(--server, tools/testbed_up.sh 시험대) 둘 다
전제: docs/parkchan 이 :8765.   사용: python3 tools/e2e_feedback.py [--server] [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SERVER = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
if SERVER:
    ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']
    APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'; OWNER = ('owner@parkchan.kr', 'owner-pass')
else:
    APP = 'http://127.0.0.1:8765/index.html?server='; OWNER = ('owner@parkchan.kr', '2580')
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_feedback'; os.makedirs(SC, exist_ok=True)
TAG = 'server' if SERVER else 'local'


async def main():
    if SERVER: U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); await ctx.add_init_script(NO_INTRO); s = await ctx.new_page()
        s.on('pageerror', lambda e: errs.append(str(e)))
        s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
        await auto_yes(s)
        await s.goto(APP); await s.wait_for_timeout(600)
        # ① 둘러보기(비로그인): 개념에서 '틀린 곳' → 로그인 안내
        await s.click('#goGuest'); await s.wait_for_timeout(500)
        await s.evaluate("detailIdx = dayIndex(); show('detail')"); await s.wait_for_timeout(300)
        await s.click('#v-detail [data-report]'); await s.wait_for_timeout(300)
        assert await s.locator('#fbLogin').count() == 1, '비로그인인데 로그인 안내가 없다'
        await s.click('#sheetClose'); await s.wait_for_timeout(200)
        # ② 가입 → 개념에서 틀린 곳 알리기
        await s.evaluate("authMode='start'; show('auth')"); await s.wait_for_timeout(300)
        await signup(s, '의견학생', f'fb-{TAG}@t.kr')
        cid = await s.evaluate('CONCEPTS[dayIndex()].id')
        await s.evaluate("detailIdx = dayIndex(); show('detail')"); await s.wait_for_timeout(300)
        await s.click('#v-detail [data-report]'); await s.wait_for_timeout(300)
        ref = await s.inner_text('.fbref'); assert '개념' in ref and await s.evaluate('CONCEPTS[dayIndex()].title') in ref, ref
        assert await s.get_attribute('[data-fbk="content"]', 'aria-checked') == 'true', '개념에서 열면 교재 오류가 골라져 있어야 한다'
        await s.click('#fbSend'); await s.wait_for_timeout(200); assert '내용을 적어' in await s.inner_text('#fbWarn')
        await s.fill('#fbBody', '제 번호는 050101-3123456 이에요'); await s.dispatch_event('#fbBody', 'input'); await s.click('#fbSend'); await s.wait_for_timeout(300)
        assert '주민등록번호' in await s.inner_text('#fbWarn'), '주민등록번호가 막히지 않았다'
        await s.fill('#fbBody', '두 번째 포인트의 단위가 m/s 가 아니라 m/s² 같아요'); await s.dispatch_event('#fbBody', 'input')
        assert await s.inner_text('#fbN') == str(len('두 번째 포인트의 단위가 m/s 가 아니라 m/s² 같아요'))
        await s.screenshot(path=f'{SC}/f01_{TAG}_sheet.png')
        await s.click('#fbSend'); await s.locator('.toast', has_text='원장님께 보냈어요').wait_for(timeout=4000)
        # ③ 문제 은행 문제에서 · ④ 내 정보에서(종류 바꾸기) · 힘든 마음이 담긴 글
        bid = await s.evaluate("(() => { const q = BANK.find(x => x.type === 'ox' && CONCEPTS.findIndex(c => c.lessonId === x.lessonId) === dayIndex()) || BANK.find(x => x.type === 'ox'); bs = { items:[q], i:0, pick:null, right:0, wrong:[] }; show('bank'); renderBankSession(); return q.id; })()")
        await s.click('[data-ox="O"]'); await s.wait_for_timeout(300)
        await s.click('#v-bank [data-report]'); await s.wait_for_timeout(300); assert '문제 은행' in await s.inner_text('.fbref')
        await s.fill('#fbBody', '정답이 X 인 것 같아요'); await s.click('#fbSend'); await s.wait_for_timeout(700)
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#fbOpen'); await s.wait_for_timeout(300)
        assert await s.locator('.fbref').count() == 0
        await s.click('[data-fbk="idea"]'); assert '있으면 좋겠는' in await s.get_attribute('#fbBody', 'placeholder')
        await s.fill('#fbBody', '요즘 공부가 너무 힘들어서 죽고 싶어요'); await s.click('#fbSend'); await s.wait_for_timeout(700)
        assert await s.locator('.sheet .help').count() == 1, '힘든 마음이 담긴 의견인데 상담 창구 안내가 없다'
        await s.screenshot(path=f'{SC}/f02_{TAG}_care.png'); await s.click('#sheetClose')
        # ⑤ 원장: 학생 탭 '받은 의견'
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#logout'); await s.wait_for_timeout(700)
        await s.click('#goLogin'); await s.fill('#lgEmail', OWNER[0]); await s.fill('#lgPw', OWNER[1]); await s.click('#lgGo'); await s.wait_for_timeout(1400)
        box = s.locator('#fbBox'); assert await box.get_attribute('open') is not None, '새 의견이 있으면 펼쳐져 있어야 한다'
        t = await box.inner_text()
        assert '새 3건' in t and '의견학생' in t and 'm/s²' in t and '먼저 살펴보기' in t and '문제 은행' in t, t[:500]
        assert await s.evaluate(f"refLabel('concept:{cid}')") in t
        await box.scroll_into_view_if_needed(); await s.screenshot(path=f'{SC}/f03_{TAG}_owner.png')
        # 개념 보기 → 그 개념으로
        await s.locator('#fbBox .fbrow', has_text='m/s²').locator('[data-fbgo]').click(); await s.wait_for_timeout(400)
        assert await s.evaluate('view') == 'detail' and await s.evaluate('CONCEPTS[detailIdx].id') == cid
        await s.click('.tab[data-v="admin"]'); await s.wait_for_timeout(900)
        await s.locator('#fbBox .fbrow', has_text='m/s²').locator('[data-fbdone]').click(); await s.wait_for_timeout(900)
        t = await s.locator('#fbBox').inner_text(); assert '새 2건' in t and '되돌리기' in t, t[:300]
        assert not errs, errs
        print(f'FEEDBACK E2E OK ({TAG}) · 콘솔 오류', errs); await b.close()

asyncio.run(main())
