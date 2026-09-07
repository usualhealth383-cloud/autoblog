#!/usr/bin/env python3
"""대표 제품명 → 식약처 낱알 사진 URL 매핑 (content/productImages.json).

낱알식별 DB(docs/yakson/data/pills.json)와 e약은요 인덱스에서 제품명이 일치하는 정제·캡슐 사진을 찾는다.
액제·파스·연고는 낱알 DB에 사진이 없어 매핑되지 않는다(제품허가 API의 포장 사진은 별도 키 필요).
사진 출처: 식품의약품안전처 의약품 낱알식별 정보(제작 약학정보원) — 출처 표시 후 사용.
사용: python3 yakson/tools/match_images.py   → 이후 build.py 가 DATA.productImages 로 심는다.
"""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakson' / 'data'
pills = json.loads((DATA / 'pills.json').read_text(encoding='utf-8'))
easy = json.loads((DATA / 'easy-index.json').read_text(encoding='utf-8'))
drugs = []
for f in ('drugs.json', 'drugs.part2.json'):
    drugs += json.loads((ROOT / 'content' / f).read_text(encoding='utf-8'))

def norm(s):
    s = re.sub(r'\(.*?\)', '', s); s = s.replace(' ', '').lower()
    s = re.sub(r'(\d+)\s*mg', r'\1밀리그램', s).replace('밀리그람', '밀리그램')
    return s
idx = {}
for p in pills: idx.setdefault(norm(p['n']), p)
for e in easy:
    if e['img']: idx.setdefault(norm(e['n']), e)

# 액제·외용제 등 낱알 사진이 있을 수 없는 제품은 건너뛴다(오매칭 방지)
SKIP = ('액', '시럽', '현탁', '겔', '연고', '크림', '파스', '파프', '패치', '패취', '플라스타', '분무', '스프레이', '드롭', '트로키', '캡슐(수출')
out = {}
for d in drugs:
    for pr in d.get('products', []):
        name = pr['name']
        if any(k in name for k in SKIP) and '캡슐' not in name and '정' not in name.split('(')[0]: continue
        for part in re.split(r'[·/,]', name):
            n = norm(part)
            if len(n) < 3: continue
            hits = [k for k in idx if k.startswith(n[:5])]
            if not hits: continue
            best = sorted(hits, key=lambda k: (0 if k.startswith(n) else 1, len(k)))[0]
            src = idx[best]
            if any(k in src['n'] for k in ('액', '시럽', '현탁')): continue
            out[name] = {'img': src['img'], 'match': src['n'], 'seq': src.get('seq', '')}
            break
(ROOT / 'content' / 'productImages.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(out), '개 제품 사진 매핑')
for k, v in out.items(): print(' ', k, '→', v['match'])
