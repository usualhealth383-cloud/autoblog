#!/usr/bin/env python3
"""다섯 언어 시험(10-27) — ko·en·es·ja·zh × 폭 320·390·1280. 넘침·잘림 0 · JS 오류 0 · 나라별 응급 번호 · 「번역은 의료진 검수 전」 · 한국어 남은 비율(장부용).
쓰는 법: python3 yakjido/tests/i18n.py  (빌드 뒤)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design import URL, SEED, OVER, sync_playwright
LANGS = [('ko', 'KR', '119'), ('en', 'US', '911'), ('es', 'ES', '112'), ('ja', 'JP', '119'), ('zh', 'CN', '120')]
ROUTES = ['/home', '/symptom/fever', '/symptom/headache', '/drug/acetaminophen', '/kids', '/rx/bp', '/bag', '/me?t=set', '/talk', '/together', '/supp']
HANGUL = """()=>{let a=0,k=0;const w=document.createTreeWalker(document.querySelector('#view'),NodeFilter.SHOW_TEXT);while(w.nextNode()){const t=w.currentNode.textContent.trim();if(!t||!w.currentNode.parentElement.offsetParent)continue;a++;if(/[가-힣]/.test(t))k++;}return [k,a]}"""
fails = []; rep = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    for L, CC, emg in LANGS:
        ko_left = [0, 0]
        for W in (320, 390, 1280):
            pg = b.new_page(viewport={'width': W, 'height': 860}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.add_init_script(SEED + f";localStorage.setItem('yakjido.lang','{L}');localStorage.setItem('yakjido.cc','{CC}')")
            pg.goto(URL + '#/home'); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
            if L != 'ko': pg.wait_for_function("()=>window.I18N", timeout=10000); pg.evaluate("()=>I18N.ready"); pg.wait_for_timeout(500)
            for r in ROUTES:
                pg.evaluate("h=>{location.hash=h;route()}", r); pg.wait_for_timeout(600 if r != '/talk' else 1600)
                o = pg.evaluate(OVER)
                if o: fails.append(f'{L} {W} {r} 넘침 {o}')
                if L != 'ko' and not pg.query_selector('#view .i18n-note'): fails.append(f'{L} {W} {r} 「번역 검수 전」 줄 없음')
                tels = pg.eval_on_selector_all('#view a[href^="tel:"]', 'a=>a.map(x=>x.getAttribute("href").slice(4))')
                bad = [t for t in tels if t in ('119', '911', '112', '120') and t != emg]
                if bad: fails.append(f'{L}/{CC} {W} {r} 응급 번호 {bad} (기대 {emg})')
                if W == 390 and L != 'ko': k, a = pg.evaluate(HANGUL); ko_left[0] += k; ko_left[1] += a
            er = pg.evaluate("()=>{location.hash='#/home';route();return [...document.querySelectorAll('#view a.er-line')].map(a=>a.getAttribute('href')+' '+a.innerText.slice(0,60))}")
            if W == 390: rep.append(f'{L}/{CC}: 홈 응급 줄 {er[:1]}')
            if errs: fails.append(f'{L} {W} JS 오류 {errs[:2]}')
            pg.close()
        if L != 'ko': rep.append(f'{L}: 한국어가 남은 글 덩어리 {ko_left[0]}/{ko_left[1]} ({ko_left[0]/max(1,ko_left[1]):.0%}) — 본문 번역 전 몫')
    # 영어 폰을 쓰는 한국 거주자(10-27 Main) — 나라를 고르지 않았으면 기기 시간대로: en-US + Asia/Seoul → 119
    for tz, want in (('Asia/Seoul', '119'), ('America/New_York', '911'), ('Europe/Paris', '112')):
        pg = b.new_page(locale='en-US', timezone_id=tz); pg.add_init_script(SEED)
        pg.goto(URL + '#/home'); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
        if pg.evaluate("()=>!!window.I18N"): pg.evaluate("()=>I18N.ready"); pg.wait_for_timeout(400)
        got = pg.evaluate("()=>{route();return [window.LANG, window.CC, (document.querySelector('#view a.er-line')||{}).getAttribute?.('href')]}")
        if got[2] != 'tel:' + want: fails.append(f'en-US + {tz}: 응급 번호 {got} (기대 {want})')
        else: rep.append(f'en-US + {tz} → {got[1]} · {got[2]}')
        pg.close()
    b.close()
for r in rep: print(' ', r)
if fails: print('결함', len(fails)); [print('  ✗', f) for f in fails[:40]]; sys.exit(1)
print(f'✓ 다섯 언어 × 320·390·1280 · 화면 {len(ROUTES)}개 — 넘침 0 · JS 오류 0 · 나라별 응급 번호 · 검수 전 줄')
