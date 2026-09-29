"""E2E 공통 — 첫 실행 소개 건너뛰기 · 단계별 가입."""

# 처음 여는 브라우저에서 소개(3장)를 건너뛴다 — 저장된 진도가 없을 때만 표시만 남긴다
NO_INTRO = "try { if (!localStorage.getItem('pcs.v2')) localStorage.setItem('pcs.v2', JSON.stringify({ introSeen: true })); } catch (e) {}"


async def signup(pg, name, email, pw='123456', role='student', code='', child='', u14=False, gname='', gphone='', phone='', welcome=True, wait=1300):
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
