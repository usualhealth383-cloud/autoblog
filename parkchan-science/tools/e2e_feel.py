#!/usr/bin/env python3
"""앱 손맛 E2E — 안드로이드 뒤로가기(가입은 한 단계씩, 홈에서는 두 번 눌러 종료) · 서버가 느릴 때 자리 표시 ·
당겨서 새로고침(다른 기기에서 올린 글이 바로 보임). 진짜 Postgres·PostgREST 시험대.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_feel.py [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_feel'; os.makedirs(SC, exist_ok=True)
# 안드로이드 흉내: 뒤로가기 단추를 눌렀다고 알려 주고, 앱이 끝났는지 기록한다
STUB = """window.__app = { back:null, exited:0 };
window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'android', Plugins: {
  App: { addListener: (ev, fn) => { if (ev === 'backButton') window.__app.back = fn; return { remove(){} }; }, exitApp: () => { window.__app.exited++; } } } };"""
BACK = "window.__app.back && window.__app.back()"


async def main():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True); await ctx.add_init_script(NO_INTRO); await ctx.add_init_script(STUB)
        s = await ctx.new_page(); s.on('pageerror', lambda e: errs.append(str(e))); s.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await s.goto(APP); await s.wait_for_timeout(700)
        # ① 가입 중 뒤로가기 = 한 단계 이전, 첫 단계에서는 시작 화면으로
        await s.click('#goSignup'); await s.click('[data-role="student"]'); await s.click('#suNext'); await s.check('input[name=suAge][value="14+"]'); await s.check('#agAll'); await s.click('#suNext'); await s.wait_for_timeout(150)
        assert await s.evaluate('SU.step') == 3
        await s.evaluate(BACK); await s.wait_for_timeout(150); assert await s.evaluate('SU.step') == 2, '뒤로가기가 한 단계씩이 아님'
        await s.evaluate(BACK); await s.evaluate(BACK); await s.wait_for_timeout(150); assert await s.evaluate('authMode') == 'start'
        # ② 시작 화면에서 뒤로가기: 한 번은 안내, 2초 안에 한 번 더 누르면 종료
        await s.evaluate(BACK); await s.wait_for_timeout(100)
        assert await s.evaluate('__app.exited') == 0 and '한 번 더' in await s.locator('.toast').last.inner_text(), '첫 뒤로가기에 바로 꺼짐'
        await s.evaluate(BACK); await s.wait_for_timeout(100); assert await s.evaluate('__app.exited') == 1, '두 번째에 꺼지지 않음'
        await s.evaluate('lastBack = 0')
        # 가입 → 홈(오늘)에서도 같은 규칙, 다른 탭에서는 홈으로
        await signup(s, '손맛학생', 'feel@t.kr')
        await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(200); await s.evaluate(BACK); await s.wait_for_timeout(200)
        assert await s.evaluate('view') == 'today' and await s.evaluate('__app.exited') == 1, '다른 탭에서 뒤로가기가 홈으로 안 감'
        # ③ 서버가 느릴 때 이야기를 처음 열면 자리 표시가 먼저
        async def slow(route):
            await asyncio.sleep(1.4); await route.continue_()
        await ctx.route('**/rest/v1/posts*', slow)
        await s.evaluate("DBX.setNick('손맛').then(a => ACC = a)"); await s.wait_for_timeout(300)
        await s.click('.tab[data-v="talk"]'); await s.wait_for_timeout(500)
        assert await s.locator('#v-talk .skel').count() == 1, '느린데 빈 화면'; await s.screenshot(path=f'{SC}/f01_skeleton.png')
        await s.wait_for_timeout(1800); assert await s.locator('#v-talk .skel').count() == 0 and await s.locator('#postNew').count() == 1
        await ctx.unroute('**/rest/v1/posts*', slow)
        # ④ 다른 기기에서 글이 올라옴 → 당겨서 새로고침하면 보인다
        tok = await s.evaluate('SESSION.access_token')
        U.urlopen(U.Request(GW + '/rest/v1/posts', data=json.dumps({'board': 'talk', 'title': '다른 폰에서 올린 글', 'body': '당겨서 새로고침 시험'}).encode(),
                            headers={'Content-Type': 'application/json', 'apikey': ANON, 'Authorization': 'Bearer ' + tok}, method='POST')).read()
        assert await s.locator('.pcard').count() == 0
        await s.evaluate("""() => { const mk = y => new Touch({ identifier: 1, target: document.body, clientX: 190, clientY: y });
          dispatchEvent(new TouchEvent('touchstart', { touches:[mk(120)] })); for (let y = 130; y <= 320; y += 30) dispatchEvent(new TouchEvent('touchmove', { touches:[mk(y)] }));
          dispatchEvent(new TouchEvent('touchend', { touches:[] })); }""")
        await s.wait_for_timeout(1200)
        assert await s.locator('.pcard').count() == 1 and '다른 폰에서' in await s.locator('.pcard').inner_text(), '당겨서 새로고침이 안 됨'
        # 조금만 당기면 새로고침하지 않는다
        n = await s.evaluate('renderSeq')
        await s.evaluate("""() => { const mk = y => new Touch({ identifier: 2, target: document.body, clientX: 190, clientY: y });
          dispatchEvent(new TouchEvent('touchstart', { touches:[mk(120)] })); dispatchEvent(new TouchEvent('touchmove', { touches:[mk(150)] })); dispatchEvent(new TouchEvent('touchend', { touches:[] })); }""")
        await s.wait_for_timeout(400); assert await s.evaluate("getComputedStyle(document.getElementById('ptr')).opacity") == '0'
        assert not errs, errs
        print('FEEL E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
