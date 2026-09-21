#!/usr/bin/env python3
"""대표 제품명 → 식약처 제품 사진 URL 매핑 (content/productImages.json).

자료 두 가지를 쓴다.
  - 낱알식별(pills.json 5,660 · pills-rx.json 19,034) : 알약 사진. img 는 id 라 URL 을 조립한다.
  - e약은요(easy-index.json)                          : 포장 사진 URL. 시럽·연고·스프레이도 여기에 있다.

맞추는 순서
  ① 이름 그대로   ② 제형 낱말을 뗀 이름   ③ 앞자리 일치
  ④ «부분 일치» — 식약처 제품명은 앞에 회사 이름이 붙는 일이 많다(후시딘연고 → 동화후시딘연고).
  ⑤ 성분으로 — 앱이 적어 둔 성분명이 제품명·성분란에 들어 있는 같은 제형의 사진.

사진 출처: 식품의약품안전처 의약품 낱알식별·의약품개요정보(e약은요) — 출처 표시 후 사용.
사용: python3 yakjido/tools/match_images.py   → 이후 build.py 가 DATA.productImages 로 심는다.
"""
import json, re, pathlib, glob, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
URL = 'https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/'

def load(name): return json.loads((DATA / name).read_text(encoding='utf-8'))

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

FORM = r'(정제|연질캡슐|경질캡슐|캡슐|캅셀|정|현탁액|건조시럽|시럽|내복액|액|겔|크림|연고|산|과립|좌약|좌제|점안액|안연고|트로키|파스|파프|카타플라스마|플라스타|첩부제|패치|패취|분무제|분무액|스프레이|나잘|점비액|질정|네일라카)\d*%?$'
def stem(s):
    x = norm(s)
    for _ in range(2): x = re.sub(FORM, '', x)
    return re.sub(r'\d+%?$', '', x)

from pharmform import formclass          # 제형 갈래 — 사진을 바꿔 달면 안 되는 단위
def liquidish(t): return formclass(t)

cands = [(p['n'], p['img'], p.get('seq', ''), p.get('ingr', '')) for p in pills if p.get('img')]
cands += [(e['n'], e['img'], e.get('seq', ''), ' '.join(e.get('i', []))) for e in easy if e.get('img')]

BY_NORM, BY_STEM = {}, {}
for n, img, seq, ing in cands:
    BY_NORM.setdefault(norm(n), (n, img, seq))
    BY_STEM.setdefault(stem(n), (n, img, seq))

def pick(name, ingredient=''):
    n, st = norm(name), stem(name)
    for key, table in ((n, BY_NORM), (st, BY_STEM)):
        if len(key) >= 3 and key in table: return table[key]
    if len(st) >= 3:
        hits = [k for k in BY_STEM if k.startswith(st)] or [k for k in BY_STEM if st.startswith(k) and len(k) >= 4]
        if hits:
            best = sorted(hits, key=lambda k: (abs(len(k) - len(st)), len(k)))[0]
            return BY_STEM[best]
        # ④ 회사 이름이 앞에 붙은 제품을 잡는다 — 같은 제형끼리만
        sub = [(n2, im, sq) for n2, im, sq, _ in cands if st in stem(n2) and liquidish(name) == liquidish(n2)]
        if sub:
            return sorted(sub, key=lambda t: len(t[0]))[0]
    # ⑤ 성분으로 — «제품 이름 안에» 성분명이 들어간 같은 제형의 사진만.
    #    성분란까지 보면 엉뚱한 약이 잡힌다(콜히친 → 오젠정 같은 사고가 났다).
    ing = norm(ingredient)
    if len(ing) >= 4 and not ing.startswith('비타민'):
        sub = [(n2, im, sq) for n2, im, sq, g in cands
               if ing in norm(n2) and liquidish(name) == liquidish(n2)]
        if sub: return sorted(sub, key=lambda t: len(t[0]))[0]
    return None

out, skipped = {}, []
for d in drugs:
    for pr in d.get('products', []):
        raw = str(pr.get('name', ''))
        if not raw: continue
        amount = str(pr.get('amount', ''))
        ing = re.split(r'[ ,·+]', amount.strip())[0] if amount else ''
        for part in re.split(r'[·/,]| 등$', raw):
            part = part.strip().rstrip('등').strip()
            if len(norm(part)) < 3: continue
            got = pick(part, ing)
            if not got: continue
            srcname, img, seq = got
            if liquidish(part) != liquidish(srcname): continue
            out[raw] = {'img': img, 'match': srcname, 'seq': seq}
            break
        else:
            skipped.append(raw)

(ROOT / 'content' / 'productImages.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(out), '개 제품 사진 매핑 ·', len(set(skipped)), '개 못 찾음')
