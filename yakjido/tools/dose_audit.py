#!/usr/bin/env python3
"""약 사전의 복용법을 식약처 허가 용법용량(e약은요 원문)과 나란히 놓는다.

자동으로 옳고 그름을 가리지 않는다 — 제형·함량이 제각각이라 기계가 판정하면 틀린다.
사람이 한 화면에서 「앱이 적은 것 ↔ 허가사항 원문」을 비교하기 위한 표다.

  python3 yakjido/tools/dose_audit.py > yakjido/용량-대조표.md
"""
import json, glob, os, re, sys
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
    n += 1
    app = ' · '.join(f"{k}: {v}" for k, v in dose.items() if v)
    print(f"\n## {d['name']}\n")
    print(f"- **앱**: {app}")
    for it in prods[:2]:
        print(f"- 식약처 「{it['n']}」: {spaced(detail(it['id']).get('u'))[:330]}")
print(f"\n---\n\n대조한 약 {n}개.")
