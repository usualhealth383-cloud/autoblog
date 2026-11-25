"""11-25 현욱님 결정(약손을 접고 약지도로) — 약손 겹침 자료를 약지도 2층으로 옮긴다.
읽는 것: yozm-health med/약손_앱/_약지도로/겹침_성분.json · 겹침_분류.json(약손 쪽 정본, 지우지 않음)
쓰는 것: yakjido/content/interactions.layer2.json (2층 · 출처 「확인중」 · 보임 false 는 숨김으로 남김)
규칙: 1층(interactions.json)과 같은 짝이면 1층이 이기고 2층에서 뺀다. 방향은 적힌 그대로. 출처를 지어내지 않는다."""
import json, re, sys, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
Y = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '/home/user/yozm-health/med/약손_앱/_약지도로')
S = json.load(open(Y / '겹침_성분.json', encoding='utf-8'))['규칙']
C = json.load(open(Y / '겹침_분류.json', encoding='utf-8'))['규칙']
ING = json.load(open(ROOT / 'content/ingredients.json', encoding='utf-8'))['ing']
R1 = json.load(open(ROOT / 'content/interactions.json', encoding='utf-8'))['rules']
core = lambda n: re.sub(r'\s|\(.*?\)|（.*?）', '', n or '').split('·')[0].split('/')[0]
idx = {}
for e in ING:
    for n in [e['n']] + e.get('aka', []): idx.setdefault(core(n), e)
def ing_of(n):
    c = core(n)
    if not c: return None
    if c in idx: return idx[c]
    for k, e in idx.items():
        if len(k) >= 3 and (k in c or (len(c) >= 3 and c in k)): return e
    return None
def side(n):
    """성분이면 k, 갈래면 괄호 속 예시 성분들이 함께 가진 cls"""
    e = ing_of(n)
    inner = re.findall(r'[(（](.*?)[)）]', n or '')
    ex = [ing_of(x) for x in re.split(r'[·,、]|\s등', inner[0])] if inner else []
    ex = [x for x in ex if x]
    if len(ex) >= 2:
        common = set(ex[0].get('cls', []))
        for x in ex[1:]: common &= set(x.get('cls', []))
        common -= {'sed', 'supp'}
        if common: return {'n': n, 'cls': sorted(common)}
    if e: return {'n': n, 'k': e['k']}
    return {'n': n}
GKW = [('항응고', ['anticoag']), ('항혈소판', ['antiplt']), ('NSAID', ['nsaid']), ('소염진통', ['nsaid']), ('MAO', ['maob']), ('감초', ['herbal-licorice']),
       ('QT', ['qt']), ('피임약', ['hormone']), ('에스트로겐', ['hormone']), ('수면제', ['sed']), ('신경안정제', ['sed']), ('진정제', ['sed']), ('항히스타민', ['anti1']),
       ('항우울', ['antidep', 'ssri']), ('항부정맥', ['antiarrhythmic']), ('코막힘', ['decongest']), ('기침 억제', ['cough']), ('알파차단', ['alpha']),
       ('오피오이드', ['opioid']), ('혈당약', ['dm']), ('피브레이트', ['fibrate']), ('젬피브로질', ['fibrate']), ('항진균', ['azole']), ('ARB', ['arb']),
       ('PPI', ['ppi']), ('국소마취', ['anesthetic-top']), ('점안액', ['eye']), ('스테로이드', ['steroid'])]
def side2(n):
    s = side(n)
    if s.get('k') or s.get('cls'): return s
    cl = sorted({c for w, cs in GKW if w in (n or '') for c in cs})
    return dict(s, cls=cl) if cl else s
def m(s, group):
    for g in group:
        if g.startswith('k:'):
            if s.get('k') == g[2:]: return True
        else:
            if g in (s.get('cls') or []): return True
            if s.get('k') and g in next((e.get('cls', []) for e in ING if e['k'] == s['k']), []): return True
    return False
def in1(a, b):
    for r in R1:
        nd = r.get('need')
        if nd and len(nd) == 2 and ((m(a, nd[0]) and m(b, nd[1])) or (m(b, nd[0]) and m(a, nd[1]))): return r['id']
        if r.get('count') and (m(a, [r['count']['tag']]) and m(b, [r['count']['tag']])): return r['id']
    return None
pairs, drop, hitc = [], 0, collections.Counter()
for r in S:
    a, b = side(r['a이름']), side(r['b이름'])
    h = in1(a, b)
    if h: drop += 1; hitc[h] += 1; continue
    pairs.append({'id': r['id'], 'a': a, 'b': b, '방향': 'both' if r.get('양쪽') else r.get('방향', 'a→b'), 'why': r.get('why', ''), '원문': r.get('원문', []), '보임': bool(r.get('보임')), '층': 2, '출처': '확인중'})
groups, gdrop = [], 0
for i, r in enumerate(C):
    a = side(r['성분이름']); p = side2(r['상대'])
    food = r.get('갈래') == '음식·기호품'
    if r.get('갈래') == '같은 성분 중복' and in1(a, a): gdrop += 1; continue
    if not food and in1(a, p): gdrop += 1; continue
    groups.append({'id': 'g%03d' % i, 'a': a, '상대': p if not food else {'n': r['상대']}, '갈래': r.get('갈래'), 'why': r.get('why', ''), '원문': r.get('원문', ''), '보임': bool(r.get('보임')), '층': 2, '출처': '확인중'})
HY = [('돕습니다', '도와요'), ('않습니다', '않아요'), ('없습니다', '없어요'), ('있습니다', '있어요'), ('됩니다', '돼요'), ('합니다', '해요'), ('입니다', '이에요')]
def tidy(x):
    if isinstance(x, list): return [tidy(v) for v in x]
    if isinstance(x, dict): return {k: tidy(v) for k, v in x.items()}
    if isinstance(x, str):
        for a_, b_ in HY: x = x.replace(a_, b_)
        return re.sub(r'(\d)(mg|g|mL|ml|kg|정|시간)\b', r'\1 \2', x)
    return x
DUP = json.load(open(Y / '중복_주의.json', encoding='utf-8'))['규칙'] if (Y / '중복_주의.json').exists() else []
dups = [{'id': 'd%02d' % i, 'a': side2(r['성분이름']), 'b': side2(r['같은축이름']), '말투': r.get('말투', ''), '원문': r.get('원문', []), '보임': bool(r.get('보임')), '층': 2, '출처': '확인중'} for i, r in enumerate(DUP)]
pairs = tidy(pairs); groups = tidy(groups); dups = tidy(dups)
can = lambda s: bool(s.get('k') or s.get('cls'))
out = {'meta': {'about': '2층 — 약손(11-25 접음)에서 옮긴 겹침. 출처는 모두 확인중이라 화면에서 단정하지 않는다. 보임 false 는 숨김(데이터는 남김). 1층과 같은 짝은 뺐다.', 'from': 'yozm-health med/약손_앱/_약지도로 (11-25)'}, 'pairs': pairs, 'groups': groups, 'dups': dups}
(ROOT / 'content/interactions.layer2.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
P = [p for p in pairs]; G = [g for g in groups]
print('1층', len(R1))
print('성분 짝 %d → 1층과 겹쳐 뺌 %d · 2층 %d (걸림 가능 %d · 안 걸림 %d / 보임 %d · 숨김 %d)' % (len(S), drop, len(P), sum(can(p['a']) and can(p['b']) for p in P), sum(not (can(p['a']) and can(p['b'])) for p in P), sum(p['보임'] for p in P), sum(not p['보임'] for p in P)))
print('  겹친 1층:', hitc.most_common(10))
print('분류 %d → 1층과 겹쳐 뺌 %d · 새 칸 %d (약 갈래 걸림 가능 %d · 음식 %d · 안 걸림 %d / 보임 %d · 숨김 %d)' % (len(C), gdrop, len(G), sum(g['갈래'] != '음식·기호품' and can(g['a']) and can(g['상대']) for g in G), sum(g['갈래'] == '음식·기호품' for g in G), sum(g['갈래'] != '음식·기호품' and not (can(g['a']) and can(g['상대'])) for g in G), sum(g['보임'] for g in G), sum(not g['보임'] for g in G)))
print('중복 주의 %d → 따로 칸(겹침 표에 안 넣음): 걸림 가능 %d · 보임 %d' % (len(dups), sum(can(d['a']) and can(d['b']) for d in dups), sum(d['보임'] for d in dups)))
