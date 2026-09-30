"""E2E 공통 — 첫 실행 소개 건너뛰기 · 단계별 가입."""

# 처음 여는 브라우저에서 소개(3장)를 건너뛴다 — 저장된 진도가 없을 때만 표시만 남긴다
NO_INTRO = "try { if (!localStorage.getItem('pcs.v2')) localStorage.setItem('pcs.v2', JSON.stringify({ introSeen: true })); } catch (e) {}"


async def signup(pg, name, email, pw='pass1234', role='student', code='', child='', u14=False, gname='', gphone='', phone='', welcome=True, wait=1300):
    """단계별 가입: 누구 → 약관(+나이) → 계정 → 내 정보(+보호자) → 학원 코드 → 환영"""
    await pg.click('#goSignup'); await pg.wait_for_timeout(150)
    await pg.click(f'[data-role="{role}"]'); await pg.click('#suNext'); await pg.wait_for_timeout(100)
    if role == 'student':
        await pg.check(f'input[name=suAge][value="{"u14" if u14 else "14+"}"]'); await pg.wait_for_timeout(80)
    await pg.check('#agAll'); await pg.wait_for_timeout(80); await pg.click('#suNext'); await pg.wait_for_timeout(100)
    await pg.fill('#suEmail', email); await pg.fill('#suPw', pw); await pg.click('#suNext'); await pg.wait_for_timeout(100)
    await pg.fill('#suName', name)
    if phone: await pg.fill('#suPhone', phone)
    if u14:
        await pg.fill('#suGName', gname); await pg.fill('#suGPhone', gphone)
    if role == 'owner':
        await pg.click('#suGo')
    else:
        await pg.click('#suNext'); await pg.wait_for_timeout(100)
        if role == 'student' and code: await pg.fill('#suCode', code)
        if role == 'parent' and child: await pg.fill('#suChild', child)
        await pg.click('#suGo' if (code or child) else '#suSkipCode')
    await pg.wait_for_timeout(wait)
    if welcome and await pg.locator('#welcomeGo').count():
        await pg.click('#welcomeGo'); await pg.wait_for_timeout(900)


# 앱은 기기 기본 confirm() 대신 앱 안 확인 시트(#askYes)를 쓴다. 시험에서는 뜨는 대로 '확인'을 누른다.
# 직접 누르는 시험을 하려면 페이지에서 window.__askManual = true.
AUTO_YES = ("(() => { if (window.__autoYes) return; window.__autoYes = 1; new MutationObserver(() => { if (window.__askManual) return; "
            "const b = document.getElementById('askYes'); if (b && !b.dataset.auto){ b.dataset.auto = 1; setTimeout(() => b.click(), 60); } })"
            ".observe(document, { childList: true, subtree: true }); })()")


async def auto_yes(pg):
    await pg.add_init_script(AUTO_YES)
    try:
        await pg.evaluate(AUTO_YES)
    except Exception:
        pass


async def approve_child(pg, code, gw='http://127.0.0.1:8767'):
    """보호자 연결은 원장 확인 뒤 열린다(2026-10-01) — 시험에서 원장 대신 확인을 누르고 보호자 화면을 새로 그린다.
    로컬 모드: 같은 기기 저장소에서 바로 확인 · 서버 모드: 원장 계정으로 guardian_decide"""
    mode = await pg.evaluate('DBX.mode')
    if mode == 'local':
        await pg.evaluate(f"(async () => {{ await DBX.guardianDecide(ACC.id, '{code}', true); ACC = await DBX.me(); }})()")
    else:
        import json, urllib.request as U
        anon = json.loads(U.urlopen(gw + '/__anon').read())['anon']
        tok = json.loads(U.urlopen(U.Request(gw + '/auth/v1/token?grant_type=password', data=json.dumps({'email': 'owner@parkchan.kr', 'password': 'owner-pass'}).encode(), headers={'Content-Type': 'application/json', 'apikey': anon}, method='POST')).read())['access_token']
        uid = await pg.evaluate('ACC.id')
        U.urlopen(U.Request(gw + '/rest/v1/rpc/guardian_decide', data=json.dumps({'p_uid': uid, 'p_code': code, 'p_ok': True}).encode(), headers={'Content-Type': 'application/json', 'apikey': anon, 'Authorization': 'Bearer ' + tok}, method='POST')).read()
        await pg.evaluate("(async () => { ACC = await DBX.me(); })()")
    await pg.evaluate("show('parent')"); await pg.wait_for_timeout(900)
