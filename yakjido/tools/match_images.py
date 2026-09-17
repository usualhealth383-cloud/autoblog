#!/usr/bin/env python3
"""대표 제품명 → 식약처 제품 사진 URL 매핑 (content/productImages.json).

자료 두 가지를 쓴다.
  - 낱알식별(pills.json 5,660 · pills-rx.json 19,034) : 알약 사진. img 는 id 라 URL 을 조립한다.
  - e약은요(easy-index.json)                          : 포장 사진 URL. 시럽·연고·스프레이도 여기에 있다.

앞서 이 도구는 drugs.json·drugs.part2.json 두 파일만 읽어 36개만 매칭됐다.
지금은 drugs*.json 전부와 계열 표까지 훑는다.

사진 출처: 식품의약품안전처 의약품 낱알식별·의약품개요정보(e약은요) — 출처 표시 후 사용.
사용: python3 yakjido/tools/match_images.py   → 이후 build.py 가 DATA.productImages 로 심는다.
"""
import json, re, pathlib, glob
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
URL = 'https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/'

def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))

pills = load('pills.json') + load('pills-rx.json')
for p in pills:
    if p.get('img') and not str(p['img']).startswith('http'): p['img'] = URL + str(p['img'])
easy = load('easy-index.json')

drugs = []
for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
    drugs += json.loads(pathlib.Path(f).read_text(encoding='utf-8'))

def norm(s):
    s = re.sub(r'\(.*?\)', '', str(s))
    s = re.sub(r'[\s·,／/]+', '', s).lower()
    s = re.sub(r'(\d+)\s*mg', r'\1밀리그램', s)
    return s.replace('밀리그람', '밀리그램').replace('미리그램', '밀리그램')

# 제형 낱말은 이름 끝에서 떼어 내고 비교한다(제품 표기가 제각각이라)
FORM = r'(정제|연질캡슐|경질캡슐|캡슐|캅셀|정|현탁액|건조시럽|시럽|내복액|액|겔|크림|연고|산|과립|좌약|좌제|점안액|안연고|트로키|파스|파프|카타플라스마|플라스타|첩부제|패치|패취|분무제|스프레이|나잘|점비액|질정)\d*$'
def stem(s):
    x = norm(s)
    for _ in range(2): x = re.sub(FORM, '', x)
    return x

# 사진 후보: 낱알(알약) + e약은요(포장). 같은 이름이면 낱알을 먼저 둔다.
cands = []
for p in pills:
    if p.get('img'): cands.append((p['n'], p['img'], p.get('seq', ''), 'pill'))
for e in easy:
    if e.get('img'): cands.append((e['n'], e['img'], e.get('seq', ''), 'easy'))

BY_NORM, BY_STEM = {}, {}
for n, img, seq, kind in cands:
    BY_NORM.setdefault(norm(n), (n, img, seq, kind))
    BY_STEM.setdefault(stem(n), (n, img, seq, kind))

# 액제·외용제에 알약 사진이 붙는 오매칭을 막는다
LIQUID = ('액', '시럽', '현탁', '겔', '연고', '크림', '스프레이', '분무', '점안', '파스', '파프', '카타플라스마', '플라스타', '첩부', '패치', '패취', '좌약', '좌제', '질정')
def liquidish(t): return any(k in t for k in LIQUID)

def pick(name):
    """제품 이름 하나에 맞는 사진을 고른다 — 완전 일치 → 제형 뗀 일치 → 앞자리 일치."""
    n, st = norm(name), stem(name)
    for key, table in ((n, BY_NORM), (st, BY_STEM)):
        if len(key) >= 3 and key in table: return table[key]
    if len(st) < 3: return None
    hits = [k for k in BY_STEM if k.startswith(st)] or [k for k in BY_STEM if st.startswith(k) and len(k) >= 4]
    if not hits: return None
    best = sorted(hits, key=lambda k: (abs(len(k) - len(st)), len(k)))[0]
    return BY_STEM[best]

out, skipped = {}, []
for d in drugs:
    for pr in d.get('products', []):
        raw = str(pr.get('name', ''))
        if not raw: continue
        for part in re.split(r'[·/,]| 등$', raw):
            part = part.strip().rstrip('등').strip()
            if len(norm(part)) < 3: continue
            got = pick(part)
            if not got: continue
            srcname, img, seq, kind = got
            # 제형이 어긋나면 버린다(먹는 약에 파스 사진이 붙는 일)
            if liquidish(part) != liquidish(srcname): continue
            out[raw] = {'img': img, 'match': srcname, 'seq': seq}
            break
        else:
            skipped.append(raw)

(ROOT / 'content' / 'productImages.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(out), '개 제품 사진 매핑 ·', len(set(skipped)), '개 못 찾음')
