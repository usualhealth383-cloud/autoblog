# 약 설명(보이기만 하는 칸) GPT 번역 묶음 — 만들기·반영 (11-05 Main 「길동무 꼴 GPT 번역 묶음」)
#   만들기: python3 yakjido/tools/gpt_drug.py make      → yakjido/GPT_번역/약지도_<1~4>.txt + 약지도_열쇠.json
#   답:     현욱님이 GPT 답을 세션에 붙여 넣으면 yakjido/GPT_번역/약지도_<번호>_답.txt 로 저장(표 밖 글이 섞여도 됨 — 「Y1-001 | …」 줄만 읽음, 칸은 | 또는 탭)
#   반영:   python3 yakjido/tools/gpt_drug.py apply        → 읽기·검사만(바꾸지 않음)
#           python3 yakjido/tools/gpt_drug.py apply --정말 → i18n/drug/{L}.json · _src-drug.json · i18n/{L}.json 의 drug 에 더함
#   ⛔ 용량·주의·금기·같이 먹기·simple(판정·약사 카드가 읽는 칸)은 이 묶음에 넣지 않는다 — 세션이 한국어 원문 보존 장치와 함께 직접.
#   ⛔ 이미 번역이 있는 약은 덮지 않는다. 칸(목록이면 목록 전체)이 하나라도 검사에 걸리면 그 칸은 넣지 않고 한국어로 남긴다.
#   넣은 뒤: python3 yakjido/tools/build.py · tests/data.py · tests/design.py · tests/i18n.py
import json, glob, re, sys, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
Y = os.path.join(R, 'yakjido'); OUT = os.path.join(Y, 'GPT_번역'); I = os.path.join(Y, 'i18n')
F = ['tagline', 'lead', 'for', 'sideEffects', 'stop', 'tips', 'faq', 'children', 'onset', 'duration']
LANGS = ('en', 'es', 'ja', 'zh')
CAP, MAXB = 4200, 4   # 한 묶음 한국어 4,200자 안팎(답이 네 말이라 길어진다) · 최대 4개

def drugs():
    d, order = {}, []
    for f in sorted(glob.glob(os.path.join(Y, 'content', 'drugs*.json')), key=lambda f: (len(f), f)):
        j = json.load(open(f, encoding='utf-8')); L = j if isinstance(j, list) else j.get('drugs', j)
        for x in L:
            if isinstance(x, dict) and 'id' in x: d[x['id']] = x; order.append(x['id'])
    return d, order

def items(k, x):
    for f in F:
        v = x.get(f)
        if isinstance(v, str) and v.strip() and v.strip() != '—': yield [k, f], v
        elif isinstance(v, list):
            for i, it in enumerate(v):
                if isinstance(it, str): yield [k, f, i], it
                elif isinstance(it, dict):
                    for q in ('q', 'a'):
                        if it.get(q): yield [k, f, i, q], it[q]

SUF = r'(연질캡슐|서방정|이중정|필름코팅정|츄어블정|현탁액|캡슐|시럽|과립|정|액|크림|연고|겔|젤|로션|패취|패치|플라스타|카타플라스마|스프레이|점안액|가글액|산)$'
STOP = {'약국', '어린이', '항생제', '처방', '일반', '복합', '나졸'}
EN_FIX = {'corn-unsap': 'unsaponifiable corn extract'}
def brands(D):
    clean = lambda e: re.sub(r'\s*\(.*?\)', '', e or '').strip().lower()
    ko2en = {}
    for k, x in D.items():
        n = re.sub(r'\s*\(.*?\)', '', x.get('name', '')).strip()
        e = EN_FIX.get(k) or clean(x.get('en'))
        if n and e and '+' not in n and not any(q.get('name', '').startswith(n) or n.startswith(q.get('name', '-')) for q in x.get('products', [])): ko2en[n] = e   # 상품 이름이 곧 약 이름인 것(게보린 등)은 성분이 아님
    def combo(amt):   # 「이부프로펜 200 mg + 파마브롬 25 mg」 → 「ibuprofen + pamabrom」
        parts = [re.sub(r'\s*[\d.,~]+\s*(mg|g|mL|㎎|IU|%|μg|mcg)?\s*(/.*)?$', '', a.strip()).strip() for a in amt.split('+')]
        en = [ko2en.get(a) or next((v for kk, v in ko2en.items() if kk in a or a in kk), None) for a in parts]
        if all(en): return 'a combination of ' + ' + '.join(en)
        k = [e for e in en if e]
        return 'a combination medicine containing ' + ' + '.join(k) if k else None
    br = {}
    for k, x in D.items():
        e = EN_FIX.get(k) or clean(x.get('en'))
        for p in x.get('products', []):
            n = re.sub(r'\s*\(.*?\)', '', p.get('name', '')).strip(); amt = p.get('amount', '')
            if '·' in n or n.endswith('등'): continue          # 「콜대원·타이레놀콜드에스 등」 같은 예시 목록은 건너뜀
            many = '+' in amt or '복합' in amt or '가지' in amt
            val = (combo(amt) if '+' in amt else None) or ('a combination medicine' if many else e)
            if not val: continue
            s0 = re.sub(SUF, '', n).strip()
            for c in {n, s0, s0.split()[0] if s0 else ''}:
                if len(re.sub('[^가-힣]', '', c)) >= 2 and c not in STOP and c not in ko2en:
                    br.setdefault(c, val)
    return br

HEAD = '''의료 앱(약 안내) 화면 문구를 옮깁니다. 아래 표의 한국어를 영어·스페인어·일본어·중국어(간체)로 옮겨, 같은 꼴 `열쇠 | en | es | ja | zh` 표로만 답하세요.
- 숫자·단위(mg, g, mL, %)는 그대로, 개수와 순서도 같게. 「100명 중 34명」 같은 빈도는 그 말의 자연스러운 꼴로(예: 34 in 100).
- **굵게** 표시(별표 두 개로 감싼 말)는 원문과 같은 수만큼, 같은 뜻의 말에. ¶ 는 문단 나눔이라 그 자리에 그대로 두세요.
- 진단·처방 문장을 새로 만들지 마세요. 원문에 없는 내용을 더하지 말고, 원문의 내용을 빼지도 마세요. 용량 숫자를 바꾸지 마세요.
- 아래 「상품명 → 성분 이름」 표의 한국 상품명은 성분 이름으로 바꾸세요(예: 뮤테란 → acetylcysteine, 각 말의 성분 이름으로). 표에 없는 한국 상품명은 소리대로 로마자로 적으세요. 답에 한글은 한 글자도 남기지 마세요.
- 한국에만 해당하는 사실(식약처 허가, 한국 약국에서 판다 등)은 in Korea · en Corea · 韓国では · 在韩国 처럼 한국 이야기라고 밝히세요. 식약처 = Korea's drug regulator(Ministry of Food and Drug Safety), 질병관리청 = Korea Disease Control and Prevention Agency.
- 119 · 109 · 1577-0199 같은 번호는 그대로 두세요.
- 말투: 환자·보호자에게 쉬운 말로 존댓말(스페인어 usted · 일본어 です・ます). 영어는 영국식 철자(diarrhoea, oesophagus).
- free · gratis · 無料 · 免费 같은 말은 쓰지 마세요. 스페인어에 « » 대신 ' ' 또는 “ ”.
- 열쇠 칸은 바꾸지 말고 그대로, 한 줄에 한 열쇠, 칸 사이는 | . 표 밖의 설명은 쓰지 마세요. 길어서 끊기면 「계속」이라고 하면 이어서 쓰세요.

답 예시:
열쇠 | en | es | ja | zh
Y1-001 | Thins phlegm | Fluidifica la flema | たんをうすく | 让痰变稀
'''

def make():
    D, order = drugs(); done = set(json.load(open(os.path.join(I, 'drug', '_src-drug.json'), encoding='utf-8')))
    txt = ' '.join(open(f, encoding='utf-8').read() for f in glob.glob(os.path.join(Y, 'content', 'symptoms*.json')))
    fr = {k: len(re.findall(r'"' + re.escape(k) + r'"', txt)) for k in D}
    rest = sorted([k for k in order if k not in done], key=lambda k: (-fr[k], order.index(k)))   # 증상 화면에 나오는 약 먼저
    br = brands(D); bundles = [[]]; size = 0; taken = []
    for k in rest:
        its = list(items(k, D[k])); n = sum(len(v) for _, v in its)
        if size + n > CAP and bundles[-1]:
            if len(bundles) == MAXB: break
            bundles.append([]); size = 0
        bundles[-1].append((k, its)); size += n; taken.append(k)
    keymap = {}; os.makedirs(OUT, exist_ok=True)
    for bi, B in enumerate(bundles, 1):
        lines, used, no = [], set(), 0
        for k, its in B:
            for path, v in its:
                no += 1; key = f'Y{bi}-{no:03d}'; keymap[key] = {'path': path, 'ko': v}
                lines.append(f'{key} | ' + re.sub(r'\n+', ' ¶ ', v))
                used |= {b for b in br if b in v}
        g = []
        for u in sorted(used, key=len, reverse=True):
            if not any(u in w for w in g): g.append(u)
        gl = '\n'.join(f'{u} → {br[u]}' for u in sorted(g)) or '(이번 묶음에는 없음)'
        open(os.path.join(OUT, f'약지도_{bi}.txt'), 'w', encoding='utf-8').write(HEAD + f'\n상품명 → 성분 이름(영어 이름 — 다른 말은 그 말의 성분 이름으로)\n{gl}\n\n열쇠 | ko\n' + '\n'.join(lines) + '\n')
        print(f'약지도_{bi}.txt · 약 {len(B)}개 · 열쇠 {no} · 한국어 {sum(len(v) for _, its in B for _, v in its)}자 · 상품명 {len(g)}')
    json.dump({'drugs': taken, 'keys': keymap}, open(os.path.join(OUT, '약지도_열쇠.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'묶음에 든 약 {len(taken)} / 남은 약 {len(rest)}')

BAN = {'en': r'\bfree\b', 'es': r'\bgratis\b|gratuit|[«»]', 'ja': r'無料', 'zh': r'免费'}
def nums(s): return sorted(re.findall(r'\d+(?:[.,]\d+)?', s.replace(',', '')))
BR = None
def check(ko, v, L):
    global BR
    if BR is None: BR = sorted(brands(drugs()[0]), key=len, reverse=True)
    e = []
    if re.search('[가-힣]', v): e.append('한글')
    if v.count('**') and ko.count('**') != v.count('**'): e.append('굵게')   # GPT 화면에서 복사하면 ** 가 통째로 사라진다 — 하나도 없으면 받는다(뜻은 같음), 수가 어긋나면 걸림
    for b in BR: ko = ko.replace(b, ' ')
    ko = re.sub(r'\d+\s*(차|세대)', ' ', ko)   # 「1차 치료」「1세대」 → first-line · first-generation 처럼 말로 바뀜   # 「이지엔6」의 6 처럼 상품 이름 속 숫자는 성분 이름으로 바뀌며 사라진다
    if len(re.findall(r'\n+', ko)) != v.count('¶'): e.append('문단')
    for n in ('119', '109', '1577-0199'):
        if ko.count(n) != v.count(n): e.append('번호 ' + n)
    if L in ('en', 'es') and nums(ko) != nums(v): e.append('숫자')   # 일·중은 한자 숫자·단위 꼴이 달라 숫자 개수만 본다
    if L in ('ja', 'zh') and len(nums(ko)) != len(nums(v)): e.append('숫자')
    if re.search(BAN[L], v, re.I): e.append('금지어')
    return e

def apply(real):
    M = json.load(open(os.path.join(OUT, '약지도_열쇠.json'), encoding='utf-8')); K = M['keys']; D, _ = drugs()
    got = {}
    for f in sorted(glob.glob(os.path.join(OUT, '약지도_*_답.txt'))):
        for line in open(f, encoding='utf-8'):
            m = re.match(r'^\s*\|?\s*(Y\d-\d{3})\s*(\t|\|)(.*)$', line.rstrip('\n'))
            if not m: continue
            body = m.group(3).replace('\\|', '\x00')   # 표 속 링크 [[drug:x\|이름]] 의 \| 는 칸 나눔이 아님
            c = [x.strip().replace('\x00', '|') for x in (body.split('\t') if m.group(2) == '\t' else body.rstrip(' |').split('|'))]
            if len(c) >= 4: got[m.group(1)] = dict(zip(LANGS, c[:4]))
    if not got: print('답 파일이 없어요 — yakjido/GPT_번역/약지도_<번호>_답.txt 로 붙여 넣어 주세요.'); sys.exit(1)
    src = json.load(open(os.path.join(I, 'drug', '_src-drug.json'), encoding='utf-8'))
    bad, out = [], {L: {} for L in LANGS}
    byfield = {}
    for key, k in K.items(): byfield.setdefault(tuple(k['path'][:2]), []).append(key)
    nfield = {L: 0 for L in LANGS}
    have = {L: json.load(open(os.path.join(I, 'drug', L + '.json'), encoding='utf-8')) for L in LANGS}
    for (d, f), keys in byfield.items():
        for L in LANGS:
            if f in have[L].get(d, {}): continue   # 이미 있는 칸은 덮지 않음
            ok, vals = True, {}
            for key in keys:
                v = got.get(key, {}).get(L)
                if not v: ok = False; break
                v = v.replace(' ¶ ', '\n\n').replace('¶', '\n\n'); e = check(K[key]['ko'], v.replace('\n\n', '¶'), L)
                if e: ok = False; bad.append(f'{key} {L} {",".join(e)} — {v[:40]}'); break
                vals[key] = v
            if not ok: continue
            o = out[L].setdefault(d, {}); orig = D[d][f]
            if isinstance(orig, str): o[f] = vals[keys[0]]
            else:
                lst = json.loads(json.dumps(orig, ensure_ascii=False))
                for key in keys:
                    p = K[key]['path']
                    if len(p) == 3: lst[p[2]] = vals[key]
                    else: lst[p[2]][p[3]] = vals[key]
                o[f] = lst
            nfield[L] += 1
    miss = sorted(set(K) - set(got))
    print(f'답 {len(got)} / 열쇠 {len(K)} · 넣을 칸 ' + ' · '.join(f'{L} {nfield[L]}' for L in LANGS) + f' · 걸린 것 {len(bad)}')
    for x in bad[:40]: print('  ✘', x)
    if miss: print(f'  · 답에 없는 열쇠 {len(miss)}개(예: {", ".join(miss[:5])}) — 답이 잘렸으면 그 묶음을 다시')
    if not real: print('(읽기만 했어요. 넣으려면 --정말)'); return
    def dump(p, d, ind):
        raw = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
    def ind(p): return 0 if open(p, encoding='utf-8').read().startswith('{\n"') else 1
    newd = sorted(set().union(*[set(out[L]) for L in LANGS]))
    p = os.path.join(I, 'drug', '_src-drug.json')
    for d in newd: src.setdefault(d, {f: D[d][f] for f in F if f in D[d]})
    dump(p, src, ind(p))
    for L in LANGS:
        p = os.path.join(I, 'drug', L + '.json'); x = json.load(open(p, encoding='utf-8'))
        for d, o in out[L].items(): x.setdefault(d, {}).update(o)
        dump(p, x, ind(p))
        p = os.path.join(I, L + '.json'); x = json.load(open(p, encoding='utf-8')); g = x.setdefault('drug', {})
        for d, o in out[L].items(): g.setdefault(d, {}).update(o)
        dump(p, x, 0 if L == 'zh' else 1)
    print(f'넣었어요 — 약 {len(newd)}개. 다음: build.py · tests/data.py · design.py · i18n.py')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['make']: make()
    elif a[:1] == ['apply']: apply('--정말' in a)
    else: print('쓰는 법: make | apply [--정말]')
