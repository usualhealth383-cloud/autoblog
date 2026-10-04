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


async def audit_extra(pg, look):
    """접근성·대비 점검용 화면 더 보기(학생 로그인 상태에서 부름): 문제 풀기(확신도 칩을 고른 채) · 채점(해설 없는 문항의
    '이 개념 다시 보기' · 확신했는데 틀림) · 원장 '처리할 것'(출석만 하고 공부 기록 없는 학생 · 안 읽은 공지). 끝나면 원장으로 로그인된 채"""
    await pg.evaluate('loadMore()'); await pg.wait_for_function('MORE.ok', timeout=15000)
    if await pg.evaluate("BANK.some(q => q.step === 'mock')"):      # 대단원 마무리 · 실전 모의고사 · 시험처럼(2026-10)
        await pg.evaluate("umPick = 'unit'; show('bank')"); await pg.wait_for_timeout(250); await look('대단원 고르기')
        await pg.evaluate("umPick = 'mock'; renderBank()"); await pg.wait_for_timeout(150); await look('모의고사 고르기')
        await pg.evaluate("startMock('1')"); await pg.wait_for_timeout(250); await pg.click('[data-mxp="2"]'); await pg.wait_for_timeout(100); await look('모의고사 풀기')
        await pg.click('#mxPause'); await pg.wait_for_timeout(100); await look('모의고사 멈춤'); await pg.click('#mxResume'); await pg.wait_for_timeout(100)
        await pg.evaluate("mockSubmit(false)"); await pg.wait_for_timeout(250); await look('모의고사 결과')
        await pg.click('[data-mxr="0"]'); await pg.wait_for_timeout(150); await look('모의고사 해설')
        await pg.evaluate("mx = null; umPick = null; S.bt = true; startBank(pickBank(1), '', true)"); await pg.wait_for_timeout(250); await look('시험처럼')
        await pg.evaluate("S.bt = false; bs = null; show('bank')"); await pg.wait_for_timeout(150)
    await pg.evaluate("startBank([BANK.find(q => q.type === 'ox' && openLessons().some(l => l.id === q.lessonId))], '')"); await pg.wait_for_timeout(300)
    await pg.click('[data-conf="s"]'); await pg.wait_for_timeout(100); await look('문제 풀기(확신)')
    await pg.evaluate("bs.items[0] = { ...bs.items[0], explain:'', wrong:'' }")
    await pg.click(f'[data-ox="{"X" if await pg.evaluate("bs.items[0].answer") == "O" else "O"}"]'); await pg.wait_for_timeout(300); await look('채점(개념 링크)')
    await pg.click('#bankQuit'); await pg.wait_for_timeout(200)
    await pg.click('.tab[data-v="me"]'); await pg.wait_for_timeout(300); await auto_yes(pg); await pg.click('#logout'); await pg.wait_for_timeout(600)
    await pg.evaluate("""(() => { const d = JSON.parse(localStorage.getItem('pcs.db.v2'));
      d.attendance.push({ code:'TUE456', date:todayISO(), time:'18:00', late:false, manual:true });
      d.notices.unshift({ id:'n-audit', cls:'전체', t:'점검 공지', d:'', at:new Date(Date.now() - 5 * 36e5).toISOString(), read:[] });
      localStorage.setItem('pcs.db.v2', JSON.stringify(d)); })()""")
    await pg.reload(); await pg.wait_for_timeout(800)
    await pg.evaluate("authMode = 'login'; authErr = ''; show('auth')"); await pg.wait_for_timeout(300)   # 로그아웃 뒤에는 손님 '오늘' 화면이다
    await pg.click('[data-demo^="owner"]'); await pg.click('#lgGo'); await pg.wait_for_timeout(1200)
    await pg.wait_for_selector('#todoBox .todo-row', timeout=8000); await look('원장 처리할 것')


async def member(pg, days=30, gw='http://127.0.0.1:8767', aged=False, trust=True):
    """이야기 글쓰기는 학원 코드나 이용권이 있는 학생 계정만(2026-10, docs/11 §12-9) — 시험용 학생에게 이용권 기간을 넣는다.
    로컬 모드: 같은 기기 저장소에서 이용권 코드를 만들어 등록 · 서버 모드: 서비스 키로 profiles.pass_until
    aged=True: 가입 이틀 전으로(서버는 가입 하루가 지나야 신고를 받는다)
    trust=True: 첫 글 검토(docs/11 §12-6)를 이미 지난 학생으로 — 검토 흐름 자체는 trust=False 로 따로 시험한다"""
    if await pg.evaluate('DBX.mode') == 'local':
        await pg.evaluate(f"(async () => {{ const p = await DBX.issuePass({days}); await DBX.redeemPass(p.code); {'await DBX._trust();' if trust else ''} ACC = await DBX.me(); talkSt = null; }})()")
        return
    import json, urllib.request as U, datetime
    svc = json.loads(U.urlopen(gw + '/__anon').read())['service']
    uid = await pg.evaluate('ACC.id'); until = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    U.urlopen(U.Request(f'{gw}/rest/v1/profiles?id=eq.{uid}', data=json.dumps({'pass_until': until, **({'created_at': (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)).isoformat()} if aged else {}), **({'first_ok_at': datetime.datetime.now(datetime.timezone.utc).isoformat()} if trust else {})}).encode(), headers={'Content-Type': 'application/json', 'apikey': svc, 'Authorization': 'Bearer ' + svc}, method='PATCH')).read()
    await pg.evaluate("(async () => { ACC = await DBX.me(); talkSt = null; })()")
