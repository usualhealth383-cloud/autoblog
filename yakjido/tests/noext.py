#!/usr/bin/env python3
"""바깥 파일 0 시험(10-27 · 중국·인터넷 막힌 곳) — 바깥 주소를 모두 막은 브라우저로 첫 실행 → 주요 화면. JS 오류 0 · 글꼴이 묶음 안 Pretendard 로 · 바깥으로 나간 요청(막힌 것) 목록.
쓰는 법: python3 yakjido/tests/noext.py  (빌드 뒤)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design import URL, SEED, sync_playwright
ROUTES = ['/home', '/symptom/fever', '/drug/acetaminophen', '/kids', '/rx/bp', '/bag', '/together', '/me?t=set', '/talk', '/search?q=타이레놀', '/pill', '/login']
OK_OPTIONAL = ('open-meteo.com', 'medinanum.com', 'nedrug.mfds.go.kr')   # 연결되면 보이는 덤 — 날씨 · 형제 앱 통합 찾기 목록 · 식약처 낱알 사진(막혀도 화면·찾기는 그대로)
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    for L in ('ko', 'zh'):
        ctx = b.new_context(viewport={'width': 390, 'height': 844}); out = []
        ctx.route('**/*', lambda r: (out.append(r.request.url) or r.abort()) if not r.request.url.startswith(URL) else r.continue_())
        ctx.add_init_script(SEED + (f";localStorage.setItem('yakjido.lang','{L}');localStorage.setItem('yakjido.cc','CN')" if L != 'ko' else ''))
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL + '#/home'); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
        for r in ROUTES:
            pg.evaluate("h=>{location.hash=h;route()}", r); pg.wait_for_timeout(700)
            if pg.evaluate("()=>document.querySelector('#view').innerText.length") < 40: fails.append(f'{L} {r} 빈 화면')
        if L == 'ko':
            pg.evaluate("()=>document.fonts.ready"); f = pg.evaluate("()=>[...document.fonts].filter(f=>f.family.includes('Pretendard')&&f.status==='loaded').length")
            if not f: fails.append('Pretendard 글꼴이 묶음 안에서 안 실림')
        # 로그인 프로그램도 묶음 안에서
        ok = pg.evaluate("()=>fetch('vendor/supabase.js').then(r=>r.ok)")
        if not ok: fails.append('vendor/supabase.js 없음')
        bad = sorted({u.split('/')[2] for u in out if not any(h in u for h in OK_OPTIONAL)})
        if bad: fails.append(f'{L} 바깥으로 나간 요청: {bad}')
        if errs: fails.append(f'{L} JS 오류 {errs[:3]}')
        print(f'{L}: 화면 {len(ROUTES)}개 · 막힌 바깥 요청 {len(out)}개({sorted({u.split("/")[2] for u in out})})')
        ctx.close()
    b.close()
if fails: print('결함', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 바깥 파일 0 — 바깥 막고 첫 실행·화면', len(ROUTES) * 2, '개 · JS 오류 0 · 글꼴 묶음 안')
