#!/usr/bin/env python3
"""끊김·만료 E2E — 서버가 안 닿을 때 한국어로 알리는가, 로그인이 만료되면 로그인 화면으로 가는가, 버튼 실패가 조용히 묻히지 않는가.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_resilience.py [--shots 폴더]
"""
import asyncio, sys, os, json, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
GW = 'http://127.0.0.1:8767'; ANON = json.loads(U.urlopen(GW + '/__anon').read())['anon']
APP = f'http://127.0.0.1:8765/index.html?server={GW}&key={ANON}'
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_resilience'; os.makedirs(SC, exist_ok=True)


async def main():
    U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
        ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); s = await ctx.new_page()
        s.on('pageerror', lambda e: errs.append(str(e)))
        await auto_yes(s)
        await s.goto(APP); await s.wait_for_timeout(700)
        # ① 서버가 안 닿을 때 로그인 → 한국어 안내(영어 'Failed to fetch' 금지)
        await ctx.route(lambda url: '8767' in url, lambda r: asyncio.ensure_future(r.abort()))
        await s.click('#goLogin'); await s.fill('#lgEmail', 'x@t.kr'); await s.fill('#lgPw', 'pass1234'); await s.click('#lgGo'); await s.wait_for_timeout(800)
        e = await s.locator('.auth .err').inner_text(); assert '인터넷' in e and 'fetch' not in e.lower(), e
        await s.screenshot(path=f'{SC}/r01_offline_login.png'); await ctx.unroute_all()
        # 가입 → 이야기 글 하나
        await signup(s, '끊김학생', 'net@t.kr')
        await s.evaluate("DBX.setNick('끊김닉').then(a => ACC = a)"); await s.wait_for_timeout(300)
        await s.evaluate("DBX.addPost({ board:'talk', title:'연결 시험', body:'연결 시험 글입니다' })"); await s.wait_for_timeout(300)
        await s.click('.tab[data-v="talk"]'); await s.wait_for_timeout(700); await s.click('.pcard'); await s.wait_for_timeout(700)
        # ② 버튼을 눌렀는데 서버가 끊김 → 조용히 묻히지 않고 알림
        await ctx.route(lambda url: '8767' in url, lambda r: asyncio.ensure_future(r.abort()))
        await s.click('#pLike'); await s.wait_for_timeout(700)
        t = await s.locator('.toast').last.inner_text(); assert '인터넷' in t, t
        assert await s.locator('.netbar').count() == 1, '연결 안내 띠가 없다'
        await ctx.unroute_all()
        # ③ 로그인 만료(되살림 토큰도 무효) → 로그인 화면 + 이유
        await s.evaluate("SESSION.access_token = 'expired.' + SESSION.access_token.split('.')[1] + '.bad'; SESSION.refresh_token = 'gone'; saveSession()")
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('.tab[data-v="talk"]'); await s.wait_for_timeout(1500)
        assert await s.evaluate('view') == 'auth' and '만료' in await s.locator('.auth .err').inner_text(), await s.evaluate('view')
        await s.screenshot(path=f'{SC}/r02_session_expired.png')
        await s.fill('#lgEmail', 'net@t.kr'); await s.fill('#lgPw', 'pass1234'); await s.click('#lgGo'); await s.wait_for_timeout(1200)
        assert await s.evaluate('view') == 'today' and await s.evaluate('ACC.nick') == '끊김닉'
        # ⑤ 내 기록 내려받기(열람권): 계정·학습·이야기 글이 들어 있고 계정 id 는 빠진다
        await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(400)
        async with s.expect_download() as dl: await s.click('#myExport')
        f = await dl.value; j = json.loads(open(await f.path(), encoding='utf-8').read())
        assert j['계정']['email'] == 'net@t.kr' and 'id' not in j['계정'] and j['이야기']['글'][0]['title'] == '연결 시험' and '학습' in j, list(j)
        # ④ 권한 없는 요청의 영어 오류도 한국어로
        m = await s.evaluate("api('/rest/v1/passes', { method:'POST', body:{ code:'HACK01', days:365 } }).then(()=>'ok').catch(e => e.message)")
        assert '권한' in m, m
        # ⑥ 운영 스위치: 최소 버전보다 낮으면 막는 창(바깥을 눌러도 안 닫힘) · 안내 문구는 한 번만
        import psycopg2
        db = psycopg2.connect('host=127.0.0.1 port=54329 user=postgres dbname=pcs'); db.autocommit = True; cur = db.cursor()
        cur.execute("insert into private.config values ('min_version','9.0.0') on conflict (k) do update set v = excluded.v")
        await s.reload(); await s.wait_for_timeout(1500)
        assert '업데이트가 필요합니다' in await s.locator('.sheet h3').inner_text(); await s.screenshot(path=f'{SC}/r03_force_update.png')
        await s.mouse.click(195, 60); await s.wait_for_timeout(300); assert await s.locator('#sheetLock').count() == 1, '업데이트 창이 닫혀 버림'
        cur.execute("delete from private.config where k = 'min_version'")
        cur.execute("insert into private.config values ('notice','10월 3일 새벽 2시~4시 서버 점검이 있습니다') on conflict (k) do update set v = excluded.v")
        await s.reload(); await s.wait_for_timeout(1500)
        assert '서버 점검' in await s.locator('.sheet').inner_text(); await s.click('#sheetClose')
        await s.reload(); await s.wait_for_timeout(1500); assert await s.locator('.sheet').count() == 0, '안내가 매번 뜸'
        cur.execute("delete from private.config where k = 'notice'")
        assert not errs, errs
        print('RESILIENCE E2E OK · 콘솔 오류', errs); await b.close()

asyncio.run(main())
