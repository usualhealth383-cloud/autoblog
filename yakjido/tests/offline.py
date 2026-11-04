#!/usr/bin/env python3
"""기내 모드 시험(10-27) — 설정 「기내에서 쓰기」로 받아 둔 뒤 인터넷을 끊고 주요 화면을 연다. JS 오류 0 · 화면 비지 않음 · 인터넷 없음 띠.
쓰는 법: python3 yakjido/tests/offline.py  (빌드 뒤)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design import URL, SEED, sync_playwright
ROUTES = ['/home', '/symptom/headache', '/symptom/fever', '/drug/acetaminophen', '/search?q=타이레놀', '/bag', '/kids', '/rx', '/rx/bp', '/kinds/bp', '/supp', '/drugs', '/me?t=set', '/myths', '/about']
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    for lang in ('ko', 'en'):
        ctx = b.new_context(viewport={'width': 390, 'height': 800}, service_workers='allow')
        ctx.add_init_script(SEED + f";localStorage.setItem('yakjido.lang','{lang}')")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL + '#/home'); pg.wait_for_function("()=>navigator.serviceWorker.controller", timeout=20000)
        pg.reload(); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
        line = pg.evaluate("()=>document.querySelector('.gn-home')?.textContent||''")
        if '기내' not in line and lang == 'ko': fails.append(f'{lang} 홈 작은 줄 없음')
        pg.evaluate("()=>{location.hash='#/me?t=set';route()}"); pg.wait_for_selector('#gn-box .btn', timeout=15000)
        size = pg.evaluate("()=>document.querySelector('.gn-tot')?.textContent")
        pg.click('#gn-box .btn'); pg.wait_for_function("()=>localStorage.getItem('yakjido.offline')", timeout=180000)
        st = pg.evaluate("()=>JSON.parse(localStorage.getItem('yakjido.offline'))")
        ctx.set_offline(True)
        pg.reload(); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
        for r in ROUTES:
            pg.evaluate("h=>{location.hash=h;route()}", r); pg.wait_for_timeout(700)
            t = pg.evaluate("()=>document.querySelector('#view')?.innerText.length||0")
            if t < 80: fails.append(f'{lang} {r} 화면이 비었어요({t}자)')
        band = pg.evaluate("()=>document.querySelector('.netbar')?.textContent||''")
        if lang == 'ko' and '인터넷 없이 쓰는 중' not in band: fails.append(f'띠 글 없음: {band[:40]}')
        # 낱알 식별 자료가 캐시에서 열리는지
        ok = pg.evaluate("()=>fetch(dataPath('pills.json')).then(r=>r.ok).catch(()=>false)")
        if not ok: fails.append(f'{lang} 낱알 자료가 인터넷 없이 안 열림')
        if errs: fails.append(f'{lang} JS 오류 {errs[:3]}')
        print(f'{lang}: {size.strip()} · 받음 {st["b"]/1048576:.1f} MB · 화면 {len(ROUTES)}개')
        ctx.close()
    b.close()
if fails: print('결함', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 기내 모드 — 받아 두기 · 인터넷 끊고 화면', len(ROUTES) * 2, '개 · JS 오류 0')
