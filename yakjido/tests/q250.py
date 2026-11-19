"""현욱님 ChatGPT 질문 250(tests/q/약지도_질문_1.tsv · 11-18) — 고치기 전 점수부터. 목록은 바꾸지 않는다.
잣대(질문 갈래별 · 기계로 잴 수 있는 것만 — 답 글의 «질»은 사람이 본다):
 · 응급 38: 묻기 첫 답(__답짓기)이 응급 카드(위험)이고 119·응급실·병원 연락이 있어야 통과(11-18 Main). 없으면 «응급 놓침». (찾기 화면 맨 아래 안전 줄은 늘 있으므로 따로 셈)
 · 같이 먹어도 되나 38: 답에 조심 말(겹침·조심·간격·확인·상의 …)이 있으면 통과 · 「괜찮아요·겹치지 않아요」만 있으면 «거짓 안심» · 답 없음은 «모름»
 · 그 밖 174: 답이 있나(모름 0이 목표) · 갈래 열쇠말(아이 용량→몸무게·나이, 임신·수유→임신·수유, 보관→보관·기한·약국 …)이 답에 있나 · 거짓 안심 0
쓰는 법: python3 yakjido/tests/q250.py (빌드 뒤) — 답 전부를 tests/q/약지도_질문_1_답.tsv 로 남긴다"""
import http.server, socketserver, threading, functools, pathlib, sys, re, json, collections
from playwright.sync_api import sync_playwright
H = pathlib.Path(__file__).resolve().parent; D = H.parents[1] / 'docs' / 'yakjido'
SET = sys.argv[1] if len(sys.argv) > 1 else '250'   # 250(전부) · 200(고칠 것) · 50(잣대 — 고칠 때 보지 않는다: 줄마다 답은 출력하지 않음)
FN = {'250': '약지도_질문_1.tsv', '200': '약지도_질문_1_고칠200.tsv', '50': '약지도_질문_1_잣대50.tsv',
      '1000': '약지도_질문_2.tsv', '2고칠': '약지도_질문_2_고칠200.tsv', '2잣대': '약지도_질문_2_잣대800.tsv', '2차': '약지도_질문_2_고칠2차_응급.tsv'}[SET]   # 11-19 GPT 질문 251~1250 · 2차 = 잣대 응급 중 짝수 번호 50을 옮김(나머지는 잣대)
RULER = SET in ('50', '2잣대')
Q = [l.split('\t') for l in (H / 'q' / FN).read_text().strip().split('\n')[1:]]
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && D.drugs && D.drugs.length && window.__답짓기")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    R = pg.evaluate("""L=>L.map(q=>{let a=null; try{a=window.__답짓기(q)}catch(e){a={err:String(e)}}
      const tx=x=>Array.isArray(x)?x.map(tx).join(' / '):x&&typeof x==='object'?(x.t||x.말||x.글||x.n||''):String(x||'');
      const r=search(q)[0];
      return {w:a&&a.위험?tx(a.위험.말)+' '+tx(a.위험.할||''):'', f:a?(a.결||''):'', h:a?tx(a.할||[]):'', n:!a, err:a&&a.err||'', top:r?(r.t||'')+' '+(r.h||''):''}})""", [r[1] for r in Q])
    b.close()
srv.shutdown()
EMG = re.compile(r'119|응급실|병원(에)?\s*(바로\s*)?연락|치료\s*병원|109')
CAU = re.compile(r'겹|조심|안\s*돼|안\s*되|피하|피해|상의|확인|간격|띄워|띄어|출혈|주의|함께\s*드시지|같은\s*성분|부딪|줄어|떨어|올라|높아|위험|금기|처방의|약사')
SAFE = re.compile(r'괜찮아요|드셔도\s*돼요|겹치지\s*않|부딪히지\s*않|안\s*보여요|걱정\s*없')
KEY = {'아이 용량': r'몸무게|나이|kg|개월|어린이|아이', '임신·수유': r'임신|수유', '보관·유통기한': r'보관|기한|약국|버리|개봉|폐의약품',
       '영양제': r'영양제|비타민|칼슘|철분|마그네슘|오메가|유산균|홍삼|비오틴|엽산|섭취', '부작용': r'부작용|진료|의사|약사|멈추|중단|119',
       '먹는 법·시간': r'먹|드세|드시|간격|시간|바르|붙|넣', '증상→약 고르기': r'약|성분|진료|물|수분', '약 이름·생김새': r'성분|이름|각인|사진|약봉투|약국|제품'}
st = collections.defaultdict(collections.Counter); bad = []
out = ['번호\t갈래\t판정\t질문\t위험 카드\t첫 줄\t할 일\t찾기 1위']
for (n, q, who, cat, em, want), r in zip(Q, R):
    txt = ' '.join([r['w'], r['f'], r['h']])
    if cat == '응급':
        ok = bool(r['w'] and EMG.search(r['w'])); v = '통과' if ok else '응급 놓침'   # 11-18 Main — 묻기 첫 답이 응급 카드여야 통과(첫 줄·안전 줄만은 놓침)
        if not ok:   # 11-19 Main — 놓침을 셋으로 나눔: 찾기 1위에만 · 답 안 안전 줄에만 · 어디에도 없음(=안전 놓침, 가장 나쁨)
            v = '응급 놓침(1위엔 있음)' if EMG.search(r['top'] or '') else '응급 놓침(답 안 줄엔 있음)' if EMG.search(r['f'] + ' ' + r['h']) else '안전 놓침'
    elif cat == '같이 먹어도 되나':
        v = '모름' if r['n'] else '통과' if CAU.search(txt) else '거짓 안심' if SAFE.search(txt) else '조심 말 없음'
    else:
        v = '모름' if r['n'] else '거짓 안심' if SAFE.search(txt) and not CAU.search(txt) else '통과' if re.search(KEY.get(cat, '.'), txt) else '갈래 빗나감'
    if r['err']: v = '오류'
    st[cat][v] += 1; st['전체'][v] += 1
    if v != '통과': bad.append((n, cat, v, q, (r['w'] or r['f'])[:60]))
    out.append('\t'.join([n, cat, v, q, r['w'], r['f'], r['h'], r['top']]).replace('\n', ' '))
if not RULER: (H / 'q' / FN.replace('.tsv', '_답.tsv')).write_text('\n'.join(out) + '\n')
for c in ['응급', '같이 먹어도 되나'] + sorted(k for k in st if k not in ('응급', '같이 먹어도 되나', '전체')) + ['전체']:
    s = st[c]; print(f'{c:10} {sum(s.values()):3} — 통과 {s["통과"]} · ' + ' · '.join(f'{k} {v}' for k, v in s.items() if k != '통과'))
if not RULER:
    print('— 통과 못 한 것 —')
    for x in bad: print(' ', *x)
sys.exit(1 if any(v for k, v in st['응급'].items() if k != '통과') or st['전체']['거짓 안심'] or st['전체']['오류'] else 0)
