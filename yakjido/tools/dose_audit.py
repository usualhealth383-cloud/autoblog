#!/usr/bin/env python3
"""약 사전의 복용법을 식약처 허가 용법용량(e약은요 원문)과 나란히 놓는다.

자동으로 옳고 그름을 가리지 않는다 — 제형·함량이 제각각이라 기계가 판정하면 틀린다.
사람이 한 화면에서 「앱이 적은 것 ↔ 허가사항 원문」을 비교하기 위한 표다.

  python3 yakjido/tools/dose_audit.py > yakjido/용량-대조표.md
"""
import json, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pharmform import formclass, LABEL, norm   # 겔 자리에 파스 용법을 놓지 않기 위해
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.path.dirname(ROOT), 'docs', 'yakjido', 'data')
drugs = [x for f in sorted(glob.glob(os.path.join(ROOT, 'content', 'drugs*.json')))
         for x in json.load(open(f, encoding='utf-8'))]
idx = json.load(open(os.path.join(DATA, 'easy-index.json'), encoding='utf-8'))
SH = {}
def detail(i):
    b = i // 200
    if b not in SH: SH[b] = json.load(open(os.path.join(DATA, f'easy-{b}.json'), encoding='utf-8'))
    return SH[b][i % 200]

def spaced(t):
    """식약처 원문은 띄어쓰기가 없다 — 읽을 수 있게 숫자·단위 앞뒤를 띄운다."""
    t = (t or '').replace('\n', ' / ')
    t = re.sub(r'(?<=[가-힣])(?=\d)', ' ', t)
    t = re.sub(r'(?<=\d)(?=[가-힣])', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

print('# 복용법 ↔ 식약처 허가 용법 대조\n')
print('왼쪽은 앱이 화면에 적은 것, 오른쪽은 식약처 허가사항 원문(e약은요)이에요. ')
print('제품마다 함량이 다르므로 숫자가 달라 보여도 틀린 것이 아닐 수 있습니다 — **정수·횟수·하루 최대량**이 어긋나는지를 봅니다.\n')
n = 0
for d in sorted(drugs, key=lambda x: x['id']):
    dose = d.get('dose') or {}
    if not dose: continue
    # 앱이 이어 둔 단일 성분 제품만 — 복합제 용법은 성분 용량이 아니다
    prods = [it for it in idx if d['id'] in it.get('map', []) and len(set(it.get('i', []))) == 1]
    if not prods: continue
    # 제형이 같은 것만 — 겔을 적어 두고 파스 용법을 나란히 놓으면 대조가 안 된다
    want = {formclass(pr.get('name', '')) for pr in (d.get('products') or [])} or {'solid'}
    same = [it for it in prods if formclass(it['n']) in want]
    # 앱이 적어 둔 제품과 이름이 같은 것을 앞으로 — 같은 성분·같은 제형이라도
    # 쓰임이 다른 제품이 섞인다(클로르헥시딘은 가글과 수술 소독액이 같은 액제다)
    mine = [norm(pr.get('name', '')) for pr in (d.get('products') or []) if pr.get('name')]
    def near(it):
        n = norm(it['n'])
        return 0 if any(m and (n.startswith(m) or m in n) for m in mine) else 1
    same.sort(key=near)
    n += 1
    app = ' · '.join(f"{k}: {v}" for k, v in dose.items() if v)
    print(f"\n## {d['name']}\n")
    print(f"- **앱**: {app}")
    if same:
        for it in same[:2]:
            print(f"- 식약처 「{it['n']}」({LABEL[formclass(it['n'])]}): {spaced(detail(it['id']).get('u'))[:330]}")
    else:
        kinds = ', '.join(sorted({LABEL[formclass(it['n'])] for it in prods}))
        want_l = ', '.join(sorted({LABEL[w] for w in want}))
        print(f"- **같은 제형의 허가사항을 못 찾았습니다** — 앱은 「{want_l}」인데 자료에 있는 것은 「{kinds}」뿐이에요. 직접 확인이 필요합니다.")
print(f"\n---\n\n대조한 약 {n}개.")
