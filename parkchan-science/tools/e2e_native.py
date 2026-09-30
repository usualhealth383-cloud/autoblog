#!/usr/bin/env python3
"""앱(네이티브) 기능 E2E — 스토어 결제·구매 복원·푸시 등록/해제·오류 자동 기록을, 가짜 네이티브 플러그인을 끼운 브라우저로
진짜 시험대(Postgres·PostgREST) + 진짜 Deno 함수(verify-purchase·push) + 가짜 Google 에 붙여 끝까지 돌린다.

전제: docs/parkchan 이 :8765 에, tools/testbed_up.sh 시험대가 :8767 에 떠 있다.   사용: python3 tools/e2e_native.py [--shots 폴더]
"""
import asyncio, sys, os, json, datetime as dt, urllib.request as U
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testbed_functions as tf
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import signup, NO_INTRO, auto_yes
SC = sys.argv[sys.argv.index('--shots')+1] if '--shots' in sys.argv[:-1] else '/tmp/e2e_native'; os.makedirs(SC, exist_ok=True)
GW = tf.GW
STUB = """
window.__iap = { next: '', purchases: [], calls: [] }; window.__push = { asked: 0, registered: 0 }; window.__secure = [];
const L = {};
window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'android', Plugins: {
  NativePurchases: {
    getProducts: async ({ productIdentifiers }) => ({ products: productIdentifiers.map(id => ({ identifier:id, title:id, priceString:{ pass_m1:'₩9,900', pass_m6:'₩49,000', pass_y1:'₩79,000' }[id] })) }),
    purchaseProduct: async (o) => { window.__iap.calls.push(o); if (window.__iap.next === 'CANCEL') throw new Error('User cancelled');
      const t = window.__iap.next; const r = { productIdentifier:o.productIdentifier, purchaseToken:t, transactionId:'GPA.'+t }; window.__iap.purchases.push(r); return r; },
    getPurchases: async () => ({ purchases: window.__iap.purchases }),
  },
  SecureScreen: { set: async ({ on }) => { window.__secure.push(on); } },
  PushNotifications: {
    addListener: (ev, fn) => { L[ev] = fn; return { remove(){} }; },
    checkPermissions: async () => ({ receive: window.__push.asked ? 'granted' : 'prompt' }),
    requestPermissions: async () => { window.__push.asked++; return { receive:'granted' }; },
    createChannel: async () => {},
    register: async () => { window.__push.registered++; setTimeout(() => L.registration && L.registration({ value:'fcm-device-1' }), 30); },
  },
}};
"""


def svc(path):
    from urllib.parse import quote
    return json.loads(U.urlopen(U.Request(GW + '/rest/v1/' + quote(path, safe='?=&,.*:/()'), headers={'apikey': B['anon'], 'Authorization': 'Bearer ' + B['service']})).read())


async def main():
    global B
    B = tf.boot(); U.urlopen(U.Request(GW + '/__reset', method='POST')).read()
    APP = f"http://127.0.0.1:8765/index.html?server={GW}&key={B['anon']}"
    today = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); errs = []
            ctx = await b.new_context(viewport={'width': 400, 'height': 820}); await ctx.add_init_script(NO_INTRO); await ctx.add_init_script(STUB); s = await ctx.new_page()
            s.on('pageerror', lambda e: errs.append(str(e)) if '시험용' not in str(e) else None)
            s.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'status of 4' not in m.text else None)
            await auto_yes(s)
            await s.goto(APP); await s.wait_for_timeout(700)
            assert await s.evaluate('isNative') is True
            await s.evaluate('CFG.push = true')
            # 가입(학원 코드 없음) — 이때는 푸시 권한을 묻지 않는다
            await signup(s, '앱학생', 'app@t.kr')
            assert await s.evaluate('__push.asked') == 0, '학원과 연결도 안 했는데 푸시 권한부터 물음'
            uid = await s.evaluate('ACC.id')
            # ① 스토어 가격 표시 → 1년 이용권 결제
            await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#goPlans'); await s.wait_for_timeout(900)
            assert '₩79,000 · 구매' in await s.locator('#v-plans').inner_text(), '스토어 가격이 안 보임'
            await s.screenshot(path=f'{SC}/n01_plans_store_price.png', full_page=True)
            await s.evaluate("__iap.next = 'CANCEL'"); await s.click('[data-buy="y1"]'); await s.wait_for_timeout(500)
            assert await s.locator('#sheetBg').count() == 0 and await s.evaluate('hasPass()') is False, '사용자가 취소했는데 오류 창이 뜨거나 열림'
            tf.buy('pass_y1', 'tok-native-000001', uid); await s.evaluate("__iap.next = 'tok-native-000001'")
            await s.click('[data-buy="y1"]'); await s.wait_for_timeout(1800)
            call = (await s.evaluate('__iap.calls'))[-1]
            assert call['productIdentifier'] == 'pass_y1' and call['productType'] == 'inapp' and call['appAccountToken'] == uid, call
            exp = (today + dt.timedelta(days=365)).isoformat()
            assert await s.evaluate('hasPass()') is True and await s.evaluate('ACC.passUntil') == exp, await s.evaluate('ACC.passUntil')
            assert await s.evaluate('fullAccess()') is True
            await s.screenshot(path=f'{SC}/n02_after_purchase.png', full_page=True)
            # ② 구매 복원: 앱이 꺼져 확인 못 한 1개월 결제 → 복원하면 30일 더, 다시 복원해도 두 번 안 늘어남
            tf.buy('pass_m1', 'tok-native-000002', uid)
            await s.evaluate("__iap.purchases.push({ productIdentifier:'pass_m1', purchaseToken:'tok-native-000002', transactionId:'GPA.2' })")
            await s.click('#iapRestore'); await s.wait_for_timeout(2000)
            exp2 = (today + dt.timedelta(days=395)).isoformat(); assert await s.evaluate('ACC.passUntil') == exp2, await s.evaluate('ACC.passUntil')
            await s.click('#iapRestore'); await s.wait_for_timeout(2000); assert await s.evaluate('ACC.passUntil') == exp2, '복원을 두 번 누르니 두 번 늘어남'
            # ③ 결제 확인 실패(남의 영수증) → 안내 창 + 복원 버튼
            tf.buy('pass_m6', 'tok-native-000003', '00000000-0000-0000-0000-000000000000'); await s.evaluate("__iap.next = 'tok-native-000003'")
            await s.click('[data-buy="m6"]'); await s.wait_for_timeout(1500)
            assert '다른 계정' in await s.locator('.sheet').inner_text() and await s.locator('.sheet #iapRestore').count() == 1
            await s.screenshot(path=f'{SC}/n03_purchase_fail.png'); await s.click('#sheetClose')
            # ④ 학원 코드를 연결하는 순간 푸시 권한을 묻고 기기를 등록
            own = json.loads(U.urlopen(U.Request(GW + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json'}, method='POST')).read())['access_token']
            U.urlopen(U.Request(GW + '/rest/v1/students', data=json.dumps({'code': 'NAT001', 'name': '앱학생', 'cls': '월목반', 'until': '2099-01-01'}).encode(), headers={'Content-Type': 'application/json', 'apikey': B['anon'], 'Authorization': 'Bearer ' + own}, method='POST')).read()
            await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.fill('#codeIn', 'NAT001'); await s.click('#codeGo'); await s.wait_for_timeout(1300)
            assert await s.evaluate('__push.asked') == 1 and await s.evaluate('__push.registered') == 1
            rows = svc('push_tokens?select=token,uid'); assert rows == [{'token': 'fcm-device-1', 'uid': uid}], rows
            # 공지 → push 함수 → 이 기기로
            tf.SENT.clear()
            U.urlopen(U.Request(GW + '/functions/v1/push', data=json.dumps({'type': 'INSERT', 'table': 'notices', 'record': {'cls': '월목반', 'title': '내일 휴강', 'body': ''}}).encode(), headers={'Content-Type': 'application/json', 'x-push-secret': 'push-s'}, method='POST')).read()
            assert [m['token'] for m in tf.SENT] == ['fcm-device-1'], tf.SENT
            # ⑤ 앱 오류가 서버에 저절로 남는다(한 번만)
            for _ in range(2): await s.evaluate("setTimeout(() => { throw new Error('시험용 앱 오류') }, 0)")
            await s.wait_for_timeout(900)
            er = svc("client_errors?select=msg,ver&msg=like.*시험용*"); assert len(er) == 1 and er[0]['ver'].endswith('-app'), er
            # ⑤-2 교재·문제 화면에서만 캡처 막기(FLAG_SECURE) · 노트·이야기·내 정보는 풀기 · 교재 화면 워터마크
            async def sec(): return await s.evaluate('__secure[__secure.length-1]')
            await s.click('.tab[data-v="today"]'); await s.wait_for_timeout(300); assert await sec() is True, '오늘(교재) 화면인데 캡처가 열려 있음'
            assert not await s.evaluate("document.getElementById('wm').classList.contains('hide')"), '교재 화면에 워터마크가 없음'
            assert 'svg' in await s.evaluate("document.getElementById('wm').style.backgroundImage"), '워터마크 그림이 비어 있음'
            await s.click('.tab[data-v="talk"]'); await s.wait_for_timeout(300); assert await sec() is False, '이야기 화면은 캡처할 수 있어야 함'
            assert await s.evaluate("document.getElementById('wm').classList.contains('hide')"), '이야기 화면에 워터마크가 남음'
            await s.click('.tab[data-v="list"]'); await s.wait_for_timeout(300); assert await sec() is True
            await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); assert await sec() is False
            n = await s.evaluate('__secure.length'); await s.click('.tab[data-v="plan"]'); await s.wait_for_timeout(200)
            assert await s.evaluate('__secure.length') == n, '같은 상태면 다시 부르지 않아야 함'
            # ⑥ 로그아웃하면 이 기기 푸시 등록을 지운다(다음 사람이 앞사람 알림을 받지 않게)
            await s.click('.tab[data-v="me"]'); await s.wait_for_timeout(300); await s.click('#logout'); await s.wait_for_timeout(900)
            assert svc('push_tokens?select=token') == [], '로그아웃했는데 푸시 등록이 남음'
            assert not errs, errs
            print('NATIVE E2E OK · 콘솔 오류', errs); await b.close()
    finally:
        for pr in B['procs']: pr.terminate()

asyncio.run(main())
