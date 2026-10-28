#!/usr/bin/env python3
"""대화형 시험(10-27) — yakjido/대화/말뭉치.json: 보통 문장 뜻 맞힘 90% 이상 · 위험 문장 100% 안전 안내 먼저 · 화면 흐름(되받기·칩·119).
쓰는 법: python3 yakjido/tests/talk.py  (빌드 뒤)"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design import URL, SEED, sync_playwright
C = json.loads((pathlib.Path(__file__).resolve().parent.parent / '대화' / '말뭉치.json').read_text(encoding='utf-8'))
GRP = {'cold-combo', 'bp-rx', 'dm-rx', 'warfarin', 'analgesic'}
JUDGE = """([t, want, slots]) => { const A = window.약지도대화, b = A.봇, a = b.이해(t), st = { 값: a.값 };
  if (want.startsWith('danger')) { if (!a.위험) return 'none'; const mind = a.위험.전화 === '109'; return (want === 'danger:mind') === mind ? 'ok' : (mind ? 'mind' : '119'); }
  if (a.위험) return '위험으로 막힘: ' + a.위험.말.slice(0, 20);
  const ids = A.약찾기(t);
  if (want === 'combo') { const r = A.처리(a, st); return r && (ids.length >= 2 || /길잡이|어떤|맞으세요/.test(r.말.join(' '))) ? 'ok' : '약 ' + JSON.stringify(ids); }
  if (want.startsWith('drug:')) return ids[0] === want.slice(5) ? 'ok' : '약 ' + JSON.stringify(ids);
  const r = A.처리(a, st), txt = r ? r.말.join(' ') + ' ' + (r.칩 || []).join(' ') : '';
  if (want === 'kids') return /해열제 양 계산/.test(txt) ? 'ok' : txt.slice(0, 40);
  if (want === 'pill') return /알약 찾기/.test(txt) ? 'ok' : txt.slice(0, 40);
  if (want === 'bag') return /내 약통 열기/.test(txt) ? 'ok' : txt.slice(0, 40);
  if (want === 'together') return /둘 이상|같이/.test(txt) ? 'ok' : txt.slice(0, 40);
  if (want.startsWith('sym:')) { const s = D.symptoms.find(x => 'sym:' + x.id === want); return s && txt.includes(s.name) ? 'ok' : (txt.slice(0, 30) || '모름'); }
  return '?'; }"""
fails = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(SEED); pg.goto(URL + '#/home'); pg.wait_for_function("()=>typeof CORE!=='undefined'&&CORE===2", timeout=20000)
    if '어떤 약이 궁금하세요' not in pg.inner_text('#view'): fails.append('홈에 대화 입구 없음')
    pg.evaluate("()=>{location.hash='#/talk';route()}"); pg.wait_for_function("()=>window.약지도대화", timeout=10000); pg.wait_for_timeout(1500)
    good = 0; miss = []
    for e in C['보통']:
        r = pg.evaluate(JUDGE, [e['t'], e['뜻'], e.get('슬롯', {})])
        if r == 'ok': good += 1
        else: miss.append(f"{e['t']} → {e['뜻']} : {r}")
    rate = good / len(C['보통'])
    dok = 0; dmiss = []
    for e in C['위험']:
        r = pg.evaluate(JUDGE, [e['t'], e['뜻'], {}])
        if r == 'ok': dok += 1
        else: dmiss.append(f"{e['t']} → {e['뜻']} : {r}")
    # 다섯 언어 위험(10-27) — 나라 번호까지: 그 언어·나라로 연 페이지에서
    for L, CC, e119, mind in [('en', 'US', '911', '988'), ('es', 'ES', '112', '024'), ('ja', 'JP', '119', '0570-064-556'), ('zh', 'CN', '120', '12356')]:
        q = b.new_page(); q.add_init_script(SEED + f";localStorage.setItem('yakjido.lang','{L}');localStorage.setItem('yakjido.cc','{CC}')")
        q.goto(URL + '#/talk'); q.wait_for_function("()=>window.약지도대화&&window.I18N", timeout=20000); q.evaluate("()=>I18N.ready")
        for l2, t, want in C['위험_다국']:
            if l2 != L: continue
            r = q.evaluate("t=>{const a=약지도대화.위험(t,대화.값뽑기(t,[]));return a&&[a.전화,a.말]}", t)
            exp = mind if want == 'mind' else e119
            if not r or r[0] != exp: dmiss.append(f'{L} {t} → {want} : {r}')
            elif '119' in r[1] and e119 != '119': dmiss.append(f'{L} 안내 글에 119: {r[1][:40]}')
            else: dok += 1
        q.close()
    # 과다복용(10-28 곁에 교훈) — 이미 먹은 말은 증상 묻기 전에 119 + 「토하게 하지 마세요」, 아닌 말은 막지 않기
    NUM = {'ko': ('KR', '119'), 'en': ('US', '911'), 'es': ('ES', '112'), 'ja': ('JP', '119'), 'zh': ('CN', '120')}
    for L, t in C['과다']:
        cc, e = NUM[L]; q = b.new_page(); q.add_init_script(SEED + (f";localStorage.setItem('yakjido.lang','{L}');localStorage.setItem('yakjido.cc','{cc}')" if L != 'ko' else ''))
        q.goto(URL + '#/talk'); q.wait_for_function("()=>window.약지도대화" + ("&&window.I18N" if L != 'ko' else ''), timeout=20000)
        if L != 'ko': q.evaluate("()=>I18N.ready")
        r = q.evaluate("t=>{const a=약지도대화.위험(t,대화.값뽑기(t,[]));return a&&[a.전화,a.말]}", t); q.close()
        if not r or r[0] != e or not any(w in r[1] for w in ('토하게', 'vomit', 'vómito', '吐かせ', '催吐')): dmiss.append(f'과다 {L} {t} → {r}')
        else: dok += 1
    for t in C['과다아님']:
        r = pg.evaluate("t=>{const a=약지도대화.위험(t,대화.값뽑기(t,[]));return a&&a.말}", t)
        if r: dmiss.append(f'과다 아닌데 막음: {t} → {r[:30]}')
    print(f'보통 뜻 맞힘 {good}/{len(C["보통"])} ({rate:.0%}) · 위험 {dok}/{len(C["위험"]) + len(C["위험_다국"]) + len(C["과다"])}')
    for m in miss: print('  · 놓침', m)
    if rate < .9: fails.append(f'뜻 맞힘 {rate:.0%} < 90%')
    if dmiss: fails.append(f'위험 놓침 {dmiss}')
    # 화면 흐름
    pg.fill('.mnc-in input', '타이레놀이랑 판콜에이 같이 먹어도 돼?'); pg.click('.mnc-in button'); pg.wait_for_timeout(2500)
    t = pg.inner_text('#talk')
    if '같이 드시는지' not in t: fails.append('겹침 되받기 없음')
    if not ('조심할 것이 있어요' in t or '안 되는 것이 있어요' in t): fails.append('타이레놀+판콜에이 아세트아미노펜 겹침을 못 짚음: ' + t[-160:])
    chips = pg.eval_on_selector_all('.mnc-chips button', 'b=>b.length')
    if not 1 <= chips <= 4: fails.append(f'칩 {chips}개')
    pg.fill('.mnc-in input', '가슴이 쥐어짜듯 아프고 식은땀 나요'); pg.click('.mnc-in button'); pg.wait_for_timeout(600)
    if not pg.query_selector('.mnc-b.sos a[href="tel:119"]'): fails.append('위험 문장에 119 단추 없음')
    # 넘침 320
    pg.set_viewport_size({'width': 320, 'height': 700}); pg.wait_for_timeout(300)
    if pg.evaluate("()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1"): fails.append('320 가로 넘침')
    if errs: fails.append(f'JS 오류 {errs[:3]}')
    b.close()
if fails: print('결함', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 대화 — 뜻 맞힘 90% 이상 · 위험 100% · 겹침 되받기 · 119 · 320 넘침 0 · JS 오류 0')
