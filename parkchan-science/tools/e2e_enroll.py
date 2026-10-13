#!/usr/bin/env python3
"""학원 QR 수강 등록 · 관리자 E2E(2026-10-13 현욱님 요청).

· 원장 › 학생: '학원 QR' 상자에 QR(svg)·주소 · '새 QR로 바꾸기'
· 학원 QR 주소(?join=토큰)로 들어온 사람 → 로그인 화면 + 안내 · 주소에서 토큰이 지워진다
· 새 학생 가입 → 수강 등록 신청 시트(이름·반·연락처·개인정보 동의 필수) → 보내기 → 내 정보에 '원장님 확인 중'
· 원장 › 학생: '수강 등록 신청' → 승인(반·만료일) → 코드가 만들어져 그 계정에 연결 · 명단에 '앱' 표시
· 학생이 다시 열면 전 범위가 열린다(S.auth) · 틀린(바뀐) QR 은 안내하고 토큰을 버린다
· 원장 › 설정: 관리자 지정 → 그 계정이 원장 화면(머리 '관리자') · 관리자는 지정 칸이 없다 · 해제하면 원래 역할

전제: docs/parkchan 이 :8765 에 떠 있다. --server 면 tools/testbed_up.sh.   사용: python3 tools/e2e_enroll.py [--server]
"""
import asyncio, sys, os, json, time, urllib.request as U
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ui import NO_INTRO, auto_yes, signup
SRV = '--server' in sys.argv
GW = 'http://127.0.0.1:8767'
KEYS = json.loads(U.urlopen(GW + '/__anon').read()) if SRV else {}
APP = 'http://127.0.0.1:8765/index.html' + (f"?server={GW}&key={KEYS['anon']}" if SRV else '?server=')
OWNER = ('owner@parkchan.kr', 'owner-pass') if SRV else ('owner@parkchan.kr', '2580')
STAFF = ('enr-staff%d@t.kr' % int(time.time()), 'pass1234')
NEW = ('enr-stu%d@t.kr' % int(time.time()), 'pass1234')
SFX = str(int(time.time()) % 10000); NM = '최새봄' + SFX; NP = '폰없음' + SFX
ok = []; bad = []
def check(c, m):
    (ok if c else bad).append(m); print(('  ✓ ' if c else '  ✗ ') + m)


async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx = await br.new_context(viewport={'width': 400, 'height': 860}, locale='ko-KR')
        await ctx.add_init_script(NO_INTRO)
        pg = await ctx.new_page(); await auto_yes(pg)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        toasts = []
        await pg.expose_function('__toast', lambda t: toasts.append(t))
        await pg.add_init_script("new MutationObserver(() => { document.querySelectorAll('.toast').forEach(t => { if (t.textContent && t.dataset.seen !== t.textContent){ t.dataset.seen = t.textContent; window.__toast(t.textContent); } }); }).observe(document, { childList:true, subtree:true, characterData:true });")

        async def login(em, pw):
            if await pg.evaluate('!!ACC'): await logout()
            if await pg.locator('#goLogin').count(): await pg.click('#goLogin')
            await pg.fill('#lgEmail', em); await pg.fill('#lgPw', pw); await pg.click('#lgGo'); await pg.wait_for_timeout(1400)

        async def logout():
            await pg.evaluate("show('me')"); await pg.wait_for_timeout(300); await pg.click('#logout'); await pg.wait_for_timeout(800)

        await pg.goto(APP); await pg.wait_for_timeout(1500)
        if SRV:   # 관리자로 지정할 계정(보호자)을 먼저 만든다
            await signup(pg, '관리 담당', STAFF[0], STAFF[1], role='parent'); await logout()
        else:
            STAFF_EM = 'parent@demo.kr'
        staff_em = STAFF[0] if SRV else 'parent@demo.kr'; staff_pw = STAFF[1] if SRV else '1234'

        # ── 원장: 학원 QR ──
        await login(*OWNER); await pg.evaluate("show('admin')"); await pg.wait_for_timeout(1200)
        await pg.click('#qrBox summary'); await pg.wait_for_timeout(200)
        check(await pg.locator('#qrBox .joinqr svg').count() == 1, '원장 학생 탭: 학원 QR 그림(svg)')
        tok = await pg.evaluate('JOIN_TOK'); check(len(tok) == 10, f'QR 토큰 10자리 ({tok})')
        tip = await pg.locator('#qrBox').inner_text(); check(f'?join={tok}' in tip, 'QR 아래 주소 = 웹 주소?join=토큰')
        await pg.click('#qrNew'); await pg.wait_for_timeout(900)
        tok2 = await pg.evaluate('JOIN_TOK'); check(tok2 != tok and len(tok2) == 10, '새 QR로 바꾸기 → 토큰이 바뀐다')
        check('· ' in await pg.locator('.adm-h').inner_text() and await pg.locator('.adm-h h1').inner_text() == '원장', '머리: 원장')

        # ── 원장: 관리자 지정 ──
        await pg.click('[data-adm="settings"]'); await pg.wait_for_timeout(900)
        check(await pg.locator('#staffBox #stfAdd').count() == 1, '설정: 관리자 지정 칸(원장 본인)')
        await pg.fill('#stfEmail', staff_em); await pg.click('#stfAdd'); await pg.wait_for_timeout(1200)
        check(staff_em in await pg.locator('#staffBox').inner_text(), '관리자로 지정 → 목록에 보임')
        await logout()

        # ── 관리자 계정: 원장 화면 · 지정 칸 없음 ──
        await login(staff_em, staff_pw); await pg.wait_for_timeout(600)
        check(await pg.evaluate("ACC.role") == 'owner', '관리자 계정 역할 = 원장 화면')
        await pg.evaluate("show('admin')"); await pg.wait_for_timeout(1200)
        check(await pg.locator('.adm-h h1').inner_text() == '관리자', '머리: 관리자')
        check(await pg.locator('#qrBox').count() == 1, '관리자도 학원 QR·명단을 본다')
        await pg.click('[data-adm="settings"]'); await pg.wait_for_timeout(900)
        check(await pg.locator('#stfAdd').count() == 0, '관리자에게는 관리자 지정 칸이 없다')
        await logout()

        # ── 학원 QR 주소로 들어온 새 학생 ──
        await pg.goto(APP + f'&join={tok2}'); await pg.wait_for_timeout(1600)
        check('join=' not in pg.url, '주소에서 토큰을 지운다')
        check(await pg.evaluate("localStorage.getItem('pcs.join')") == tok2, '토큰을 기억한다')
        check(await pg.evaluate("view") == 'auth', '로그인 전이면 로그인 화면')
        check(any('학원 QR' in t for t in toasts), '안내: 가입·로그인하면 신청으로 이어짐')
        await signup(pg, NM, NEW[0], NEW[1]); await pg.wait_for_timeout(1200)
        check(await pg.locator('#enSend').count() == 1, '가입 뒤 수강 등록 신청 시트가 열린다')
        check(await pg.locator('#enName').input_value() == NM, '이름은 가입 정보로 채움')
        await pg.select_option('#enCls2', index=1); await pg.fill('#enPhone', '010-2222-3333')
        await pg.click('#enSend'); await pg.wait_for_timeout(500)
        check(any('동의' in t for t in toasts[-2:]) and await pg.locator('#enSend').count() == 1, '동의 안 하면 못 보낸다')
        await pg.check('#enAgree'); await pg.click('#enSend'); await pg.wait_for_timeout(1200)
        check(await pg.locator('#enSend').count() == 0 and any('신청했어요' in t for t in toasts), '신청 보내기')
        check(await pg.evaluate("localStorage.getItem('pcs.join')") is None, '보낸 뒤 토큰을 버린다')
        await pg.evaluate("show('me')"); await pg.wait_for_timeout(1500)
        check('원장님 확인 중' in await pg.locator('#v-me').inner_text(), '내 정보: 원장님 확인 중')
        await logout()

        # ── 원장: 승인 ──
        await login(*OWNER)
        await pg.evaluate("(async () => { const c = (await DBX.classes())[0].cls; await DBX.addStudent({ name:'" + NP + "', cls:c, until:'2027-02-28', phone:'' }); })()")   # 폰이 없는 학생 — 명단에만
        await pg.evaluate("show('admin')"); await pg.wait_for_timeout(1300)
        box = pg.locator('#enrBox'); check(await box.count() == 1 and NM in await box.inner_text(), '원장: 수강 등록 신청 1건')
        await pg.click('#enrBox [data-enok]'); await pg.wait_for_timeout(500)
        check(await pg.locator('#enGo').count() == 1, '승인 시트(반·만료일)')
        await pg.click('#enGo'); await pg.wait_for_timeout(1400)
        check(any(f'{NM} 학생 등록 · 코드' in t and '앱 연결됨' in t for t in toasts), '승인 → 코드 발급 + 앱 연결')
        stu = pg.locator('.stu', has_text=NM); check(await stu.count() == 1, '명단에 들어옴')
        check(await stu.locator('.cst.ok').count() == 1, "명단 줄에 '앱' 표시")
        check(await pg.locator('.stu', has_text=NP).locator('.cst.none').count() == 1, "앱 계정 없는 학생(폰 없음)은 '앱 없음'")
        check('명이 앱을 쓰고 있어요' in await pg.locator('#v-admin').inner_text(), '앱 사용 인원 요약')
        # 관리자 해제
        await pg.click('[data-adm="settings"]'); await pg.wait_for_timeout(900)
        await pg.click('#staffBox [data-stfdel]'); await pg.wait_for_timeout(1000)
        check(staff_em not in await pg.locator('#staffBox').inner_text(), '관리자 해제')
        await logout()
        await login(staff_em, staff_pw); check(await pg.evaluate("ACC.role") == 'parent', '해제하면 원래 역할(보호자)로'); await logout()

        # ── 학생: 다시 열면 전 범위 ──
        await login(*NEW); await pg.wait_for_timeout(800)
        check(await pg.evaluate("!!S.auth && S.auth.name === '" + NM + "'"), '승인된 학생은 로그인하면 학원 코드가 연결된다')
        # 바뀐(옛) QR
        await pg.evaluate(f"localStorage.setItem('pcs.join', '{tok}'); S.auth = null"); await pg.evaluate("maybeEnroll()"); await pg.wait_for_timeout(900)
        check(any('QR이 바뀌었' in t for t in toasts) and await pg.evaluate("localStorage.getItem('pcs.join')") is None, '옛 QR → 안내 + 토큰 버림')
        check(not errs, f'페이지 오류 없음 {errs[:2]}')
        await br.close()
    print(f'\nENROLL {"OK" if not bad else "FAIL"} {len(ok)}/{len(ok)+len(bad)}')
    sys.exit(1 if bad else 0)

asyncio.run(main())
