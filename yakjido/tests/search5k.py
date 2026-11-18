"""검색 대량 자체 시험(11-18 현욱님 «완벽한 앱으로») — 질문 5,000개 = 사람 × 주제 × 말투 격자, 500개씩 10묶음.
 · 찾기 질문(증상→약 · 약 이름 · 영양제 · 복용 시간 · 부작용): 앱 search() 의 1위 / 3위 안에 정답(증상 화면 · 그 제품 · 그 영양제)이 있나
 · 안전 질문(과량 · 임신 금기 · 아이 용량 · 응급 신호 · 같은 성분 겹침): 묻기 답(__답짓기)이 맨 위에 그 말을 하나 — 하나라도 놓치면 실패
쓰는 법: python3 yakjido/tests/search5k.py [묶음 번호 1~10 · 빼면 전부]  (빌드 뒤) · 놓친 것은 scratch 가 아니라 tests/_search5k_miss.json 에 적는다"""
import http.server, socketserver, threading, functools, pathlib, json, sys, random, re, urllib.parse
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parent; C = R.parent / 'content'; D = R.parent.parent / 'docs' / 'yakjido'
rnd = random.Random(20261118)
S = [s for f in sorted(C.glob('symptoms*.json')) for s in json.load(open(f, encoding='utf-8'))]
SUP = json.load(open(C / 'supplements.json', encoding='utf-8'))
BR = json.load(open(D / 'data' / 'brands.json', encoding='utf-8'))
# 증상 낱말 — 다른 증상과 겹치지 않는 꼬리표만(정답이 하나여야 채점이 공정하다)
tagmap = {}
for s in S:
    for t in [s['name'].split(' (')[0]] + list(s.get('tags', [])):
        t = t.strip()
        if len(t) >= 2: tagmap.setdefault(t, set()).add(s['id'])
SYM = [(t, next(iter(v))) for t, v in sorted(tagmap.items()) if len(v) == 1]
BRANDS = [b['n'] for b in BR if b.get('rx') == '일반' and 2 <= len(b['n']) <= 12]
APAP = [b['n'] for b in BR if 'apap' in (b.get('ing') or []) and b.get('rx') == '일반']
_supt = {}
for s in SUP:
    for t in [s['name']] + [x for x in s.get('tags', []) if 2 <= len(x) <= 8 and not re.search(r'[A-Z]{2,}', x)]: _supt.setdefault(t, set()).add(s['id'])
SUPS = [(t, next(iter(v))) for t, v in sorted(_supt.items()) if len(v) == 1 and t not in tagmap]   # 증상 꼬리표와 겹치는 말(감기·수면·관절)은 정답이 둘이라 뺀다
PERSONA = ['', '어르신인데 ', '엄마가 ', '아빠가 ', '고혈압약 먹는데 ', '당뇨 있는데 ', '약을 여러 개 먹는데 ', '할머니가 ', '자취생인데 ', '직장인인데 ']
def typo(w):
    if len(w) < 3: return w
    i = rnd.randrange(len(w) - 1); return w[:i] + w[i + 1] + w[i] + w[i + 2:] if rnd.random() < .5 else w[:i] + w[i + 1:]
STYLE = [lambda w, e: f'{w}{e}', lambda w, e: f'{w.replace(" ", "")}{e}', lambda w, e: f'{typo(w)}{e}',
         lambda w, e: f'{w}{e.replace("요", "예").replace("까", "꼬")}', lambda w, e: f'{w} {e.strip()}ㅠㅠ']
def q_sym():
    t, sid = rnd.choice(SYM); e = rnd.choice([' 약', ' 있어요', '에 뭐 먹어요', ' 너무 심해요', ' 약 추천', '']); st = rnd.randrange(len(STYLE))
    return {'q': rnd.choice(PERSONA) + STYLE[st](t, e), 'kind': 'sym', 'want': '/symptom/' + sid, 'typo': st == 2, 'key': t}
def q_brand(tail):
    b = rnd.choice(BRANDS); st = rnd.randrange(len(STYLE))
    return {'q': rnd.choice(PERSONA[:4]) + STYLE[st](b, tail), 'kind': 'brand', 'want': b, 'typo': st == 2, 'key': b}
def q_supp():
    t, sid = rnd.choice(SUPS); e = rnd.choice([' 먹어도 돼요', ' 효과 있어요', ' 언제 먹어요', '', ' 영양제']); st = rnd.randrange(len(STYLE))
    return {'q': rnd.choice(PERSONA[:4]) + STYLE[st](t, e), 'kind': 'supp', 'want': '/supp/' + sid, 'typo': st == 2, 'key': t}
EMERG = ['가슴이 쥐어짜듯 아파요', '숨이 안 쉬어져요', '한쪽 팔다리에 힘이 빠져요', '말이 어눌해졌어요', '피를 토했어요', '검은 변이 나와요', '벌에 쏘였는데 숨이 차요',
         '입술이 붓고 숨이 차요', '경련을 해요', '의식이 없어요', '아이가 축 처지고 안 깨요', '갑자기 벼락 치듯 머리가 아파요', '죽고 싶어요', '목숨을 끊고 싶어요']
def q_safe():
    k = rnd.choice(['od', 'od', 'preg', 'kid', 'emerg', 'emerg', 'dup'])
    if k == 'od':
        b = rnd.choice(BRANDS); t = rnd.choice(['아이가 {b} 많이 먹었어요', '애기가 {b} 한 통 다 먹었어요', '실수로 {b} 한꺼번에 10알 먹었어요', '{b} 한 통 다 먹었어', '아이가 {b}을 주워 먹었어요'])
        return {'q': t.format(b=b), 'kind': 'od'}
    if k == 'preg':
        s = rnd.choice(['두통약', '감기약', '치통', '몸살', '열 나요', '허리 아파요', '진통제'])
        return {'q': rnd.choice(['임신 중인데 ', '임산부 ', '임신했는데 ', '임신 20주인데 ']) + s, 'kind': 'preg'}
    if k == 'kid':
        w = rnd.choice([8, 10, 12, 14, 16, 18, 20, 25]); m = rnd.choice(['해열제', '타이레놀 시럽', '부루펜 시럽', '챔프'])
        return {'q': rnd.choice([f'{w}kg 아이 {m} 몇 ml', f'애기 {w}키로 {m} 얼마나 먹여요', f'우리 애 {w}kg인데 {m} 몇 미리']), 'kind': 'kid'}
    if k == 'emerg':
        return {'q': rnd.choice(PERSONA[:4]) + rnd.choice(EMERG), 'kind': 'emerg'}
    a, b = rnd.sample(APAP, 2)
    return {'q': rnd.choice(['{a}이랑 {b} 같이 먹어도 돼요', '{a} {b} 같이', '{a} 먹고 {b} 또 먹어도 돼요']).format(a=a, b=b), 'kind': 'dup'}
def batch():
    L = []
    for _ in range(500):
        r = rnd.random()
        L.append(q_sym() if r < .3 else q_brand(rnd.choice(['', ' 먹어도 돼요', ' 언제 먹어요', ' 먹고 졸려요', ' 부작용', ' 하루 몇 번', ' 식후에 먹어요'])) if r < .55 else q_supp() if r < .68 else q_safe())
    return L
BATCHES = [batch() for _ in range(10)]
JS_GRADE = r"""(L)=>L.map(x=>{
  const out={q:x.q,kind:x.kind,typo:!!x.typo,want:x.want};
  if (['sym','brand','supp'].includes(x.kind)) { let r=[]; try { r=search(x.q).slice(0,3); } catch(e) { out.err=String(e).slice(0,80); } const hit=i=>{const e=r[i]; if(!e) return false;
      if (x.kind==='brand') { const t=(e.t||'').replace(/\s/g,''), w=x.want.replace(/\s/g,''); return t.startsWith(w) || decodeURIComponent(e.h||'').replace(/\s/g,'').includes(w); }
      if (x.kind==='supp' && (e.t||'').replace(/\s/g,'').startsWith(String(x.key||'').replace(/\s/g,''))) return true;   // 제품 이름(센트룸·아로나민)으로 치면 그 제품 화면도 정답
      if (x.want==='/symptom/fever' && (e.h||'')==='/kids' && /아기|아이|애기/.test(x.q)) return true;   // 「아기 열」 → 아이 해열제 계산도 정답
      return (e.h||'').split('?')[0]===x.want; };
    out.top1=hit(0); out.top3=hit(0)||hit(1)||hit(2); out.got=r.map(e=>e.t+' '+e.h).slice(0,3); return out; }
  let a=null; try { a=window.__답짓기(x.q); } catch(e) { out.err=String(e); }
  const s=JSON.stringify(a||{}), first=a ? (a.위험 ? (a.위험.말||'') : (a.결||'')) : '';
  if (x.kind==='od') out.ok=!!(a && (a.위험 || /119|응급/.test(first)));
  else if (x.kind==='emerg') out.ok=!!(a && a.위험);
  else if (x.kind==='preg') out.ok=!!(a && /임신/.test(first) && !/이부프로펜\s*400/.test(first));
  else if (x.kind==='kid') out.ok=!!(a && (/몸무게/.test(first) || /\/kids/.test(s)));
  else if (x.kind==='dup') out.ok=!!(a && /같은 성분|안 되는|겹쳐/.test(s));
  out.first=first.slice(0,80); return out; })"""
URLB = None
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
want = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(1, 11))
rows, miss = [], []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && D.drugs && D.drugs.length && window.__답짓기")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    for n in want:
        res = pg.evaluate(JS_GRADE, BATCHES[n - 1])
        fs = [r for r in res if 'top1' in r]; sf = [r for r in res if 'ok' in r]
        t1 = sum(r['top1'] for r in fs); t3 = sum(r['top3'] for r in fs); sm = [r for r in sf if not r['ok']]
        nt = [r for r, x in zip(res, BATCHES[n - 1]) if 'top3' in r and not x.get('typo')]; print(f'  (오타 아닌 것 {len(nt)}: 1위 {sum(r["top1"] for r in nt)/max(1,len(nt))*100:.1f}% · 3위 안 {sum(r["top3"] for r in nt)/max(1,len(nt))*100:.1f}%)')
        rows.append((n, len(fs), t1, t3, len(sf), len(sm)))
        er = [r for r in res if r.get('err')]
        if er: print('오류', len(er), [r['q'] for r in er][:8], er[0]['err'])
        miss += [dict(r, 묶음=n) for r in res if ('top3' in r and not r['top3']) or ('ok' in r and not r['ok'])]
    b.close()
srv.shutdown()
print('묶음 | 찾기 질문 | 1위 | 3위 안 | 안전 질문 | 안전 놓침')
for n, a, t1, t3, s_, m in rows: print(f'{n:>2} | {a} | {t1/a*100:.1f}% | {t3/a*100:.1f}% | {s_} | {m}')
A = sum(r[1] for r in rows); print(f'합 | {A} | {sum(r[2] for r in rows)/A*100:.1f}% | {sum(r[3] for r in rows)/A*100:.1f}% | {sum(r[4] for r in rows)} | {sum(r[5] for r in rows)}')
(R / '_search5k_miss.json').write_text(json.dumps(miss, ensure_ascii=False, indent=0), encoding='utf-8')
sys.exit(1 if sum(r[5] for r in rows) else 0)
