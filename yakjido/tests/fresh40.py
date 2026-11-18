"""고치기 전에 고정한 새 말 40(11-18 Main) — 5,000 시험을 보며 고친 뒤라, 고칠 때 안 본 말로 «처음 점수»를 잰다. 이 목록은 바꾸지 않는다.
 · 찾기 30: 앱 search() 1위(·3위 안)가 기대(정규식 — 결과 제목·주소)에 맞나
 · 안전 10 + 안전이 걸린 「먹어도 돼요」 4: 묻기 답(__답짓기)의 위험 카드·첫 줄, 찾기 1위, 찾기 화면의 안전 줄 — 셋 중 어디에도 없으면 «안전 놓침»
쓰는 법: python3 yakjido/tests/fresh40.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys, re
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
F = [  # (질문, 기대 — 찾기 1위 제목·주소 정규식)
    ('할매 무릎 쑤시는데 뭐 바르노', r'근육·관절|파스|msk'), ('허리가 끊어질 것 같어', r'근육·관절|허리|msk'), ('속이 더부룩하고 신트림 나', r'체함|소화|indigestion|역류'),
    ('변이 사흘째 안 나와', r'변비'), ('밤에 잠이 안 와서 미치겠어', r'잠|수면|insomnia'), ('눈이 침침하고 뻑뻑해', r'눈|안구|dryeye'), ('입안이 헐었어', r'구내염|입안'),
    ('콧물이 줄줄 나', r'콧물|코막힘|감기'), ('기침이 안 떨어져', r'기침'), ('두드러기 올라왔어', r'두드러기|알레르기'),
    ('빨간약', r'포비돈|요오드|빨간'), ('물파스', r'물파스|파스'), ('까스활명수', r'활명수'), ('겔포스', r'겔포스'), ('우루사', r'우루사|우르소'),
    ('인사돌', r'인사돌|잇몸'), ('마데카솔', r'마데카솔'), ('후시딘', r'후시딘|푸시드'), ('판피린', r'판피린'), ('베아제', r'베아제'),
    ('술 먹고 타이레놀 먹어도 돼요', r'타이레놀|아세트아미노펜'), ('혈압약 먹는데 판콜 먹어도 돼요', r'혈압|판콜'), ('항생제랑 유산균 같이 먹어도 돼요', r'항생제|유산균'),
    ('빈속에 이부프로펜 먹어도 돼요', r'이부프로펜'), ('자기 전에 철분제 먹어도 돼요', r'철분'), ('커피랑 감기약 같이 먹어도 돼요', r'카페인|감기'),
    ('어지러워서 핑 돌아', r'어지럼'), ('발 뒤꿈치가 갈라져', r'갈라|건조|각질|발'), ('모기 물린 데 가려워', r'벌레|물림|가려움'), ('생리통 너무 심해', r'생리통')]
S = [  # (질문, 안전 낱말 — 답 첫 줄·위험 카드·1위 제목·안전 줄 어디엔가)
    ('임신인데 타이레놀 먹어도 돼요', r'임신'), ('수유 중인데 감기약 먹어도 돼요', r'수유'), ('와파린 먹는데 아스피린 먹어도 돼요', r'안 되|피|출혈|조심'),
    ('아이한테 어른 감기약 먹여도 돼요', r'아이|소아|몸무게|어린이'),
    ('가슴이 꽉 막힌 듯 답답하고 식은땀 나', r'119'), ('숨쉬기가 너무 힘들어', r'119'), ('입술이 퉁퉁 부었어', r'119'), ('애가 세제를 마셨어', r'119|중독'),
    ('할아버지가 쓰러지셨어', r'119'), ('얼굴 한쪽이 마비된 것 같아', r'119'), ('토했는데 피가 섞여 나와', r'119'), ('아기가 열 경련을 해요', r'119'),
    ('수면제 한 통을 다 먹었어', r'119|중독'), ('살고 싶지 않아', r'109')]
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && D.drugs && D.drugs.length && window.__답짓기")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    fr = pg.evaluate("L=>L.map(([q])=>search(q).slice(0,3).map(h=>(h.t||'')+' '+(h.h||'')))", F)
    sr = []
    for q, w in S:
        a = pg.evaluate("q=>{const a=window.__답짓기(q); return a ? JSON.stringify({w:a.위험?a.위험.말:'', f:a.결||''}) : '{}'}", q)
        t1 = pg.evaluate("q=>{const r=search(q)[0]; return r ? r.t+' '+r.h : ''}", q)
        pg.goto(URL + '#/search?q=' + q); pg.wait_for_timeout(700); line = pg.evaluate("()=>{const e=document.querySelector('.safe-line'); return e ? e.innerText : ''}")
        sr.append((q, w, a, t1, line))
    b.close()
srv.shutdown()
t1 = t3 = 0
for (q, w), r in zip(F, fr):
    g1 = bool(r and re.search(w, r[0])); g3 = any(re.search(w, x) for x in r); t1 += g1; t3 += g3
    print(('✓ ' if g1 else '△ ' if g3 else '✘ ') + q, '|', (r or [''])[0][:50])
miss_strict = miss = 0
for q, w, a, top, line in sr:
    card = bool(re.search(w, a)); first = bool(re.search(w, top)); ln = bool(re.search(w, line))
    miss_strict += not (card or first); miss += not (card or first or ln)
    print(('✓ ' if (card or first) else '△ ' if ln else '✘ ') + q, '| 카드' if card else '', '| 1위' if first else '', '| 안전 줄' if ln else '', '|', a[:70])
print(f'새 말 40 — 찾기 {len(F)}: 1위 {t1} · 3위 안 {t3} | 안전 {len(S)}: 놓침 {miss}(카드·1위만 보면 {miss_strict})')
sys.exit(1 if miss else 0)
